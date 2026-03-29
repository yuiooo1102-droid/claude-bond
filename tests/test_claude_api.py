from unittest.mock import patch, MagicMock

from claude_bond.utils.claude_api import classify_content, generate_questions, ask_claude


def test_ask_claude_returns_text():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Hello from Claude")]
    )
    with patch("claude_bond.utils.claude_api._get_client", return_value=mock_client):
        result = ask_claude("Say hello")
        assert result == "Hello from Claude"


def test_classify_content_calls_api():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text='{"identity": ["I am a dev"], "rules": [], "style": [], "memory": []}')]
    )
    with patch("claude_bond.utils.claude_api._get_client", return_value=mock_client):
        result = classify_content("some raw text from scanning")
        assert "identity" in result
        assert isinstance(result["identity"], list)


def test_generate_questions_calls_api():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text='["What language do you prefer?", "Short or detailed replies?"]')]
    )
    with patch("claude_bond.utils.claude_api._get_client", return_value=mock_client):
        gaps = {"style": "insufficient data"}
        result = generate_questions(gaps)
        assert isinstance(result, list)
        assert len(result) >= 1
