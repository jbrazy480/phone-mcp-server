"""Every example niche config must load and validate through the real Settings model."""

from pathlib import Path

import pytest
import yaml

from phone_mcp.config import Settings

ROOT = Path(__file__).resolve().parents[1]
NICHE_CONFIGS = sorted((ROOT / "examples" / "niches").glob("*/policy.yaml"))


def test_niche_configs_exist():
    assert len(NICHE_CONFIGS) == 5


@pytest.mark.parametrize("config_path", NICHE_CONFIGS, ids=lambda p: p.parent.name)
def test_niche_config_loads_and_validates(config_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    values = yaml.safe_load(config_path.read_text())
    settings = Settings(**values)
    assert settings.dry_run is True
    assert settings.allowed_numbers
    assert settings.caller_name and settings.caller_name != "your assistant"
    assert settings.blocklist_file is not None
    assert settings.blocklist_file.is_file()
