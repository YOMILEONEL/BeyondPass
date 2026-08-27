import pytest

from beyondpass.sandbox.docker_runner import is_docker_available

_DOCKER_AVAILABLE = is_docker_available()


def pytest_collection_modifyitems(config, items):
    if _DOCKER_AVAILABLE:
        return
    skip_docker = pytest.mark.skip(reason="Kein Docker-Daemon erreichbar")
    for item in items:
        if "docker" in item.keywords:
            item.add_marker(skip_docker)
