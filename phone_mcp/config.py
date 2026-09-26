"""Validated configuration, with explicit environment overrides."""

import os
import re
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator

E164 = re.compile(r"\+[1-9][0-9]{7,14}\Z")
PATTERN = re.compile(r"\+[1-9][0-9]{0,14}\*?\Z")


def patterns(values: list[str]) -> list[str]:
    """Require exact E.164 destinations or explicitly starred prefixes."""
    for value in values:
        if not PATTERN.fullmatch(value) or (not value.endswith('*') and not E164.fullmatch(value)):
            raise ValueError("Use E.164 numbers or a +country/area prefix ending in *")
    return values


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    dry_run: bool = True
    allowed_numbers: tuple[str, ...] = ()
    blocklist_file: Path | None = None
    max_per_hour: int = Field(default=5, ge=1, le=1000)
    max_message_length: int = Field(default=1000, ge=1, le=10000)
    caller_name: str = Field(default="your assistant", min_length=1, max_length=80)
    audit_file: Path = Path("data/audit.jsonl")
    state_file: Path = Path("data/state.sqlite3")
    twilio_account_sid: SecretStr = SecretStr("")
    twilio_auth_token: SecretStr = SecretStr("")
    twilio_from_number: str = ""
    mcp_http_token: SecretStr = SecretStr("")
    mcp_public_url: str = ""

    oauth_issuer: str = ""
    oauth_jwks_url: str = ""

    @model_validator(mode="after")
    def validate_oauth(self):
        from urllib.parse import urlparse
        if self.oauth_issuer or self.oauth_jwks_url:
            for value in (self.oauth_issuer, self.oauth_jwks_url, self.mcp_public_url):
                parsed = urlparse(value)
                if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.query or parsed.fragment:
                    raise ValueError("OAuth requires HTTPS issuer, JWKS and public resource URLs")
            if self.mcp_http_token.get_secret_value():
                raise ValueError("Choose OAuth or a static bearer token, not both")
        return self

    @field_validator("allowed_numbers")
    @classmethod
    def validate_patterns(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        patterns(list(value))
        return value

    @field_validator("caller_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip() or any(ord(c) < 32 for c in value):
            raise ValueError("Caller name must be readable text")
        return value.strip()

    @field_validator("twilio_from_number")
    @classmethod
    def validate_sender(cls, value: str) -> str:
        if value and not E164.fullmatch(value):
            raise ValueError("TWILIO_FROM_NUMBER must be E.164")
        return value


def load_settings() -> Settings:
    """Load .env and optional policy.yaml; environment takes precedence."""
    load_dotenv()
    path = Path(os.getenv("POLICY_FILE", "policy.yaml"))
    if "POLICY_FILE" in os.environ and not path.is_file():
        raise ValueError("Configured policy file is missing")
    values = yaml.safe_load(path.read_text()) if path.exists() else {}
    if values is None:
        values = {}
    if not isinstance(values, dict):
        raise ValueError("Policy must be a YAML mapping")
    for field in Settings.model_fields:
        if field.upper() in os.environ:
            value = os.environ[field.upper()]
            values[field] = tuple(x.strip() for x in value.split(',') if x.strip()) if field == "allowed_numbers" else value
    if values.get("blocklist_file") == "":
        values["blocklist_file"] = None
    return Settings(**values)
