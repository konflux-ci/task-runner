import pytest

from devtool.software_list import Package, list_packages
from tests.constants import REPO_ROOT
from tests.utils.container import Container

package_name_to_executable_name = {
    "coreutils-single": "coreutils",
    "git-core": "git",
    "findutils": "find",
    "gawk": "awk",
    "gettext-envsubst": "envsubst",
}

# overrides for tools that don't support a simple --version flag
version_arg_overrides = {
    "tkn": ["version", "--component", "client"],
}

expected_packages = list_packages(REPO_ROOT)
packages_param = [pytest.param(package, id=package.name) for package in expected_packages]


@pytest.mark.parametrize("package", packages_param)
def test_package_is_installed(package: Package, task_runner_container: Container) -> None:
    executable_name = package_name_to_executable_name.get(package.name, package.name)
    task_runner_container.run_cmd([executable_name, "--help"])


@pytest.mark.parametrize("package", packages_param)
def test_package_returns_correct_version(
    package: Package, task_runner_container: Container
) -> None:
    executable_name = package_name_to_executable_name.get(package.name, package.name)

    if executable_name == "microdnf":
        pytest.skip("microdnf doesn't have a version flag")

    version_args = version_arg_overrides.get(executable_name, ["--version"])
    proc = task_runner_container.run_cmd([executable_name, *version_args])

    if executable_name == "jq":
        pytest.xfail("jq from the RPM doesn't currently return a correct version string")

    # drop the release part from RPM versions
    expect_version, _, _ = package.version.partition("-")
    assert expect_version in proc.stdout
