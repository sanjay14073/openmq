from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    admin_api_key: str = "dev-admin-key"
    database_url: str = "sqlite+aiosqlite:///./openmq.db"
    artemis_management_url: str = "http://localhost:8161/console/jolokia"
    artemis_admin_user: str = "artemis"
    artemis_admin_password: str = "artemis"
    cors_origins: str = "http://localhost:3000"
    default_broker_name: str = "broker-1"
    default_broker_host: str = "localhost"
    default_broker_internal_host: str = "artemis"
    default_broker_stomp_port: int = 61613
    default_broker_management_url: str = "http://localhost:8161/console/jolokia"
    default_broker_messaging_host: str = "localhost"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
