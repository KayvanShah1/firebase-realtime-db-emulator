import secrets
from functools import lru_cache
from pathlib import Path

from pydantic import EmailStr, Field, SecretStr, ValidationInfo, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def find_project_root(
    markers: tuple[str, ...] = ("pyproject.toml", ".git"),
) -> Path:
    """
    Search upwards from the current file's directory to find the project root.

    This avoids fragile Path.parents[n] assumptions when files are moved.
    """
    current = Path(__file__).resolve().parent

    for parent in [current] + list(current.parents):
        if any((parent / marker).exists() for marker in markers):
            return parent

    return Path.cwd().resolve()


PROJECT_ROOT = find_project_root()
APP_DIR = PROJECT_ROOT / "app"
BASE_DIR = PROJECT_ROOT


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    # Server
    server_name: str | None = None
    server_host: str | None = None

    # Project paths
    project_root: Path = PROJECT_ROOT
    app_dir: Path = APP_DIR
    base_dir: Path = BASE_DIR
    templates_dir: Path = BASE_DIR / "templates"
    static_root: Path = BASE_DIR / "assets"

    # Authentication and security
    secret_key: SecretStr = Field(default_factory=lambda: secrets.token_urlsafe(32))
    access_token_expire_minutes: int = 60 * 24 * 8
    backend_cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    algorithm: str = "HS256"

    # Application
    project_name: str = "FireMongo"
    api_v1_prefix: str = "/api/v1"
    api_v2_prefix: str = "/api/v2"

    # Database
    mongodb_uri: SecretStr | None = None
    database_name: str = "firebase_db"

    # Email
    smtp_tls: bool = True
    smtp_ssl: bool = False
    smtp_port: int | None = None
    smtp_host: str | None = None
    smtp_user: str | None = None
    smtp_password: SecretStr | None = None
    emails_from_email: EmailStr | None = None
    emails_from_name: str | None = None
    email_reset_token_expire_hours: int = 48
    email_templates_dir: Path = BASE_DIR / "templates" / "email"
    email_test_user: EmailStr = "test@example.com"

    # Registration
    users_open_registration: bool = False

    @field_validator("secret_key", mode="before")
    @classmethod
    def generate_secret_key_when_empty(cls, value: object) -> object:
        if value is None or value == "":
            return secrets.token_urlsafe(32)
        return value

    @field_validator("emails_from_name")
    @classmethod
    def use_project_name_for_sender(cls, value: str | None, info: ValidationInfo) -> str:
        return value or info.data["project_name"]

    @computed_field
    @property
    def emails_enabled(self) -> bool:
        return bool(self.smtp_host and self.smtp_port and self.emails_from_email)

    def model_dump(self, **kwargs):
        """Custom dump to make absolute paths relative for clean logging."""
        dump = super().model_dump(**kwargs)
        project_root = self.project_root.resolve()
        for key, value in dump.items():
            if isinstance(value, Path) and value.is_absolute():
                try:
                    dump[key] = str(value.relative_to(project_root))
                except ValueError:
                    dump[key] = str(value)
        return dump


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

if __name__ == "__main__":
    from rich.pretty import pprint

    pprint(settings.model_dump())
