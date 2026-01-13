# For best results, use the same python version as the task-runner image
PYTHON_VERSION = 3.12

.PHONY: venv
venv: .venv

.PHONY: .venv
.venv:
	uv sync --python $(PYTHON_VERSION) --group dev

.PHONY: submodules
submodules:
	git submodule update --init --depth=1

RPM_IN_FILES = $(shell find . -name rpms.in.yaml)
RPM_LOCK_FILES = $(patsubst %/rpms.in.yaml,%/rpms.lock.yaml,$(RPM_IN_FILES))

# Defines separate targets for each individual **/rpms.lock.yaml file
.PHONY: $(RPM_LOCK_FILES)
$(RPM_LOCK_FILES):
	# rpm-lockfile-prototype depends on dnf bindings (the python3-dnf package on fedora)
	#   => need --system-site-packages
	uv venv --allow-existing --system-site-packages .rpm-lock-venv
	UV_PROJECT_ENVIRONMENT=.rpm-lock-venv uv run --group rpm-lock \
		rpm-lockfile-prototype $(@D)/rpms.in.yaml --outfile $@

.PHONY: all-rpm-locks
all-rpm-locks: $(RPM_LOCK_FILES)

.PHONY: pip-requirements
pip-requirements: .venv
	uv pip compile \
		--python-version $(PYTHON_VERSION) \
		--generate-hashes \
		deps/pip/requirements.in -o deps/pip/requirements.txt
	uv run pybuild-deps compile \
		--generate-hashes \
		deps/pip/requirements.txt -o deps/pip/requirements-build.txt
