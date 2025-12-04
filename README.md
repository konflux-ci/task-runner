# Task Runner Image

A container image with CLI tools commonly used by Konflux Tasks.

This project implements [ADR-0046: Common Task Runner Image].

## Purpose

The Task Runner image consolidates multiple CLI tools into a single container
image, simplifying Task creation and reducing the maintenance overhead of
managing multiple tool-specific images.

You can use it directly as the runtime image for Konflux Tasks
or as a base image for more specialized runner images.

## Included Tools

See [Installed-Software.md](Installed-Software.md) for the complete list of
tools and their versions.

## Adding New Tools

### Criteria

Tools must meet the following requirements for inclusion:

- Must be a standalone CLI tool
  - Language runtimes are also acceptable (e.g. Python)
- Must be installable [hermetically][konflux-hermetic]
- Must follow a versioning scheme (preferably semantic versioning)
- Should have release notes or a changelog

### Installation Methods

Tools are organized under `deps/` by installation method:

#### RPM Packages

RPM packages use a [lockfile-based approach][rpm-lockfile]
for hermeticity and reproducibility.

Process:

1. Add the package name to `deps/rpm/rpms.in.yaml` under either:
   - `packages` - for new packages
   - `reinstallPackages` - for packages already in the base image (we want
     control over their versions)

2. Regenerate the lockfile:

   ```sh
   make rpms.lock.yaml
   ```

3. Regenerate auto-generated files:

   ```sh
   devtool gen --all
   ```

The `install-rpms.sh` script reads the infile and the lockfile and automatically
installs the exact package versions specified.

#### Go Tools

If the tool is installable via `go install`, prefer this approach. Compared to
the [submodule approach](#git-submodules-go), this results in more accurate SBOMs.

Each tool has its own directory with `go.mod`/`go.sum`, which is crucial for independent
version management. Go's [MVS](https://go.dev/ref/mod#minimal-version-selection)
ensures we get the same versions of dependencies used upstream. Combining multiple
tools in one `go.mod` file would break that.

Process:

1. Create a directory under `deps/go-tools/` with the tool name

2. Inside, create `go.mod` and `go.sum` that reference the tool's CLI package. Example:

   ```sh
   mkdir deps/go-tools/cosign
   cd deps/go-tools/cosign
   go mod init github.com/konflux-ci/task-runner/deps/go-tools/cosign
   go get -tool github.com/sigstore/cosign/v3/cmd/cosign@v3.0.2
   go mod tidy
   ```

   Note: Use `go get -tool` (not just `go get`).
   Specify the package with the CLI binary, which is often a sub-package of the module
   (e.g. `github.com/sigstore/cosign/v3/cmd/cosign`, not `github.com/sigstore/cosign/v3`).

3. Add the tool to `install-tools.sh`:

   ```sh
   install_tool <name> [version_ldflags_attribute]
   ```

   The `version_ldflags_attribute` injects the version into the binary and
   is required for tools that use this approach (otherwise tests will fail when
   checking version output). To find the correct attribute, inspect the tool's
   upstream build process (often found in the Makefile or build scripts).

4. Regenerate auto-generated files:

   ```sh
   devtool gen --all
   ```

#### Git Submodules (Go)

If the tool is not installable with `go install`, e.g. due to the use of `replace`
directives in the tool's `go.mod` or due to incorrectly formatted semver tags,
fall back to git submodules.

Process:

1. Add the submodule and check out a semver(-ish) tag:

   ```sh
   cd deps/go-submodules
   git submodule add <repository-url> <tool-name>
   cd <tool-name>
   git checkout v1.2.3
   ```

2. In `.gitmodules`, set the `branch` field to the current tag (Renovate uses
   this for updates). If the submodule doesn't use correct semver tags (like `oc`),
   add corresponding Renovate configuration in `devtool/renovate.py` with a custom
   versioning regex.

3. Add build commands to `install-submodules.sh`

4. Regenerate auto-generated files:

   ```sh
   devtool gen --all
   ```

## Development Workflow

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Podman

### Setup

Initialize/update git submodules:

```sh
make submodules
```

Create a virtual environment and install dependencies:

```sh
make venv
source .venv/bin/activate
```

### Helper Tool

The `devtool` CLI assists with common development tasks:

```sh
devtool ls         # List all tools to be installed
devtool gen --all  # Generate files (e.g. Installed-Software.md)
```

### Building the Image

Locally:

```sh
podman build -t task-runner .
```

For production: we use Konflux CI. See the pipelines in `.tekton/`.

### Testing

Run tests to verify tool installations:

```sh
pytest
```

By default, tests build the image and tag it `localhost/task-runner:test`.
To skip rebuilding and test an existing image, set the `TEST_IMAGE` environment
variable:

```sh
# Build once
podman build -t localhost/task-runner:latest .

# Run tests against the existing image
TEST_IMAGE=localhost/task-runner:latest pytest

# Set it in .env for persistent use (if you use direnv or similar shell integration)
echo 'TEST_IMAGE=localhost/task-runner:latest' >> .env
```

Tests automatically discover packages and their expected versions using the
code in `devtool/software_list.py`. If a new package isn't detected properly,
you may need to update the discovery logic there. You may also need to update
test configuration (e.g. `version_arg_overrides` in `tests/test_installed_packages.py`
for tools that don't support the standard `--version` flag).

### Updating RPM Lockfile

After modifying `deps/rpm/rpms.in.yaml`:

```sh
make rpms.lock.yaml
```

This uses [rpm-lockfile-prototype] to resolve and lock package versions.

## Releasing

### Versioning

The version of the runner image is tracked in the VERSION file.

The Konflux build pipeline automatically sets the `org.opencontainer.image.version`
annotation (and label as well) on the built image using our custom
`.tekton/tasks/get-build-params.yaml` Task.

When making a new release, bump the version according to the first matching rule:

- Removed a tool / updated the major version of any tool -> bump the **major** version
- Added a new tool / updated the minor version of any tool -> bump the **minor** version
- Otherwise -> bump the **patch** version

To bump the version automatically based on the changes in installed software, use:

```sh
# Assuming the remote for the upstream repo is called 'upstream'
git fetch --tags upstream

devtool prep-release
```

The tool will automatically update the VERSION file and output a markdown list with
the changes since the last release. Include this list when creating the GitHub release
later.

If there are no relevant changes to the installed software (i.e. the `Installed-Software.md`
file did not change), the tool will abort without doing any changes. In that case,
if you do want to do a release, please update the VERSION file manually and write
the release notes yourself.

### Release process

1. Determine what has changed since last release and update the VERSION file accordingly
   (see above).
2. Send a PR to update the version.
3. Once merged, if the Konflux release succeeds, create a GitHub release. In the
   release notes, describe the relevant changes. You can use the output of the
   `devtool prep-release` command. If you don't have that output available, use
   `devtool diff --base-ref <previous_version> --changelog` (if this fails, you
   may need to fetch tags first).

[ADR-0046: Common Task Runner Image]: https://github.com/konflux-ci/architecture/blob/main/ADR/0046-common-task-runner-image.md
[konflux-hermetic]: https://konflux-ci.dev/docs/building/hermetic-builds/
[rpm-lockfile]: https://hermetoproject.github.io/hermeto/rpm/
[rpm-lockfile-prototype]: https://github.com/konflux-ci/rpm-lockfile-prototype
