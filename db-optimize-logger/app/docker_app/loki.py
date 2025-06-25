import docker
from docker import errors as docker_errors
from docker.client import DockerClient

from app.core.config import settings
from app.logs.logger import app_logger


def remove_loki_container(client: DockerClient) -> None:
    app_logger.info("Removing old container …")
    container = client.containers.get("dol-loki")
    container.remove(force=True)


def remove_loki_volume(client: DockerClient) -> None:
    volume = client.volumes.get("dol-loki-data")
    volume.remove(force=True)


def pull_loki_image(client: DockerClient) -> None:
    try:
        client.images.get("grafana/loki:main")
        app_logger.info("Loki image already pulled")
    except docker_errors.ImageNotFound:
        app_logger.info("Pulling loki image …")
        loki_image_tag = "grafana/loki:main"
        client.images.pull(loki_image_tag)


def start_loki_container(client: DockerClient) -> None:
    pull_loki_image(client)

    config_host_path = settings.LOKI_CONFIG_HOST_PATH
    if not config_host_path:
        raise RuntimeError("LOKI_CONFIG_HOST_PATH environment variable not set")

    container = client.containers.create(
        image="grafana/loki:main",
        name="dol-loki",
        volumes={
            "dol-loki-data": {"bind": "/var/lib/loki", "mode": "rw"},
            config_host_path: {
                "bind": "/etc/loki/local-config.yaml",
                "mode": "ro",
            },
        },
        ports={"3100/tcp": 3100},
        command=["-config.file=/etc/loki/local-config.yaml"],
        detach=True,
    )

    network = client.networks.get(settings.NETWORK)
    network.connect(container, aliases=["loki", "dol-loki"])

    container.start()

    app_logger.info("Successfully started new loki container")


def reset_loki_volume(client: DockerClient):
    remove_loki_container(client)

    remove_loki_volume(client)
    app_logger.info("Successfully resetted loki volume")


def create_docker_client() -> DockerClient:
    return docker.DockerClient.from_env()
