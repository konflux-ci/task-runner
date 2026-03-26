import logging
import os

import pytest

from tests.with_container.utils.container import Container
from tests.constants import REPO_ROOT


log = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def task_runner_container() -> Container:
    if image_name := os.getenv("TEST_IMAGE"):
        log.info("Using existing TEST_IMAGE=%s", image_name)
        return Container(image_name)

    image_name = "localhost/task-runner:test"
    log.info("Building Task Runner image (name=%s)", image_name)
    return Container.build_image(REPO_ROOT, image_name)
