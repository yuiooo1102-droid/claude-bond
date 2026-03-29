from claude_bond.utils.security import filter_secrets


def test_filters_api_keys():
    text = "My key is sk-ant-api03-abcdef123456 and also OPENAI_API_KEY=sk-proj-xyz"
    result = filter_secrets(text)
    assert "sk-ant-api03" not in result
    assert "sk-proj-xyz" not in result
    assert "[REDACTED" in result


def test_filters_env_style_secrets():
    text = """
DATABASE_URL=postgres://user:pass@host/db
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
NORMAL_VAR=hello
"""
    result = filter_secrets(text)
    assert "postgres://user:pass" not in result
    assert "wJalrXUtnFEMI" not in result
    assert "NORMAL_VAR=hello" in result


def test_preserves_normal_content():
    text = "- I am a data scientist\n- I prefer Python\n- No emoji please"
    result = filter_secrets(text)
    assert result == text


def test_filters_bearer_tokens():
    text = 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc.def'
    result = filter_secrets(text)
    assert "eyJhbGci" not in result
