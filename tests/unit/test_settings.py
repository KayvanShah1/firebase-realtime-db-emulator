import pytest
from pydantic import SecretStr

from app.core.settings import PROJECT_ROOT, Settings

pytestmark = pytest.mark.unit


def test_settings_are_loaded_from_environment(monkeypatch):
    monkeypatch.setenv("PROJECT_NAME", "Injected project")
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", '["https://example.com"]')
    monkeypatch.setenv("SMTP_TLS", "false")
    monkeypatch.setenv("SMTP_PORT", "2525")

    settings = Settings(_env_file=None)

    assert settings.project_name == "Injected project"
    assert settings.backend_cors_origins == ["https://example.com"]
    assert settings.smtp_tls is False
    assert settings.smtp_port == 2525


def test_settings_accept_constructor_overrides():
    settings = Settings(
        _env_file=None,
        project_name="Configured project",
        secret_key="configured-secret",
        mongodb_uri="mongodb://user:password@example.com/database",
        smtp_password="smtp-secret",
        smtp_host="smtp.example.com",
        smtp_port=587,
        emails_from_email="sender@example.com",
    )

    assert settings.project_name == "Configured project"
    assert isinstance(settings.secret_key, SecretStr)
    assert settings.secret_key.get_secret_value() == "configured-secret"
    assert settings.mongodb_uri is not None
    assert settings.mongodb_uri.get_secret_value() == "mongodb://user:password@example.com/database"
    assert settings.smtp_password is not None
    assert settings.smtp_password.get_secret_value() == "smtp-secret"
    assert settings.emails_from_name == "Configured project"
    assert settings.emails_enabled is True
    serialized_settings = str(settings.model_dump())
    assert "configured-secret" not in serialized_settings
    assert "user:password" not in serialized_settings
    assert "smtp-secret" not in serialized_settings


def test_empty_secret_key_is_replaced():
    settings = Settings(_env_file=None, secret_key="")

    assert settings.secret_key.get_secret_value()


def test_project_paths_are_rooted_and_dumped_as_relative_paths():
    settings = Settings(_env_file=None)

    assert settings.project_root == PROJECT_ROOT
    assert settings.app_dir == PROJECT_ROOT / "app"
    assert settings.templates_dir == PROJECT_ROOT / "templates"
    assert settings.static_root == PROJECT_ROOT / "assets"

    dumped_settings = settings.model_dump()
    assert dumped_settings["project_root"] == "."
    assert dumped_settings["app_dir"] == "app"
    assert dumped_settings["templates_dir"] == "templates"
    assert dumped_settings["static_root"] == "assets"
