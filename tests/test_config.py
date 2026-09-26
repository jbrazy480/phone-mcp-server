import pytest
from pydantic import ValidationError

from phone_mcp import check
from phone_mcp.config import Settings, load_settings


@pytest.mark.parametrize('config', [
    {'allowed_numbers': ('212',)}, {'max_per_hour':0}, {'max_message_length':0},
    {'caller_name':' '}, {'caller_name':'bad\nname'}, {'twilio_from_number':'123'},
    {'dry_run':'maybe'}, {'unknown_guard':True}, {'oauth_issuer':'http://insecure.invalid'},
])
def test_invalid_configuration(config):
    with pytest.raises(ValidationError):
        Settings(**config)


def test_env_overrides_yaml(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path/'policy.yaml').write_text('dry_run: false\nallowed_numbers: ["+1212*"]\nmax_per_hour: 3\n')
    monkeypatch.setenv('DRY_RUN', 'true')
    monkeypatch.setenv('ALLOWED_NUMBERS', '+1415*, +12125550123')
    settings = load_settings()
    assert settings.dry_run
    assert settings.allowed_numbers == ('+1415*','+12125550123')
    assert settings.max_per_hour == 3


@pytest.mark.parametrize('content', ['[]', 'unknown_guard: true'])
def test_invalid_yaml(tmp_path, monkeypatch, content):
    monkeypatch.chdir(tmp_path)
    (tmp_path/'policy.yaml').write_text(content)
    with pytest.raises(ValueError):
        load_settings()


def test_explicit_missing_policy(tmp_path, monkeypatch):
    monkeypatch.setenv('POLICY_FILE', str(tmp_path/'missing.yaml'))
    with pytest.raises(ValueError, match='missing'):
        load_settings()


def test_doctor(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert check.main() == 0
    assert 'DRY_RUN' in capsys.readouterr().out
    monkeypatch.setenv('DRY_RUN','false')
    monkeypatch.setenv('TWILIO_AUTH_TOKEN','private-test-value')
    assert check.main() == 1
    assert 'private-test-value' not in capsys.readouterr().out
