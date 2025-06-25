from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    NETWORK: str
    OPTIONAL_DOCKER_SOCK: str = "unix://var/run/docker.sock"

    LOKI_CONFIG_HOST_PATH: str


settings = Settings()  # type: ignore
