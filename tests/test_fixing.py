import pytest

from scraper.fixing import ContentFixer, get_fixer
from scraper.fixing.gemini import GeminiFixer
from scraper.fixing.ollama import OllamaFixer
from scraper.fixing.openai_fixer import OpenAIFixer
from scraper.settings import AISettings

FIXER_PROMPT_HTML = "<p>broken html<p>"


def test_gemini_fixer_calls_api_and_returns_text(mocker):
    fake_response = mocker.MagicMock()
    fake_response.text = "<p>fixed html</p>"

    fake_client_cls = mocker.patch("scraper.fixing.gemini.genai.Client")
    fake_client = fake_client_cls.return_value
    fake_client.models.generate_content.return_value = fake_response

    fixer = GeminiFixer(api_key="key-123")
    result = fixer.fix_html(FIXER_PROMPT_HTML)

    assert result == "<p>fixed html</p>"
    fake_client_cls.assert_called_once_with(api_key="key-123")
    _, kwargs = fake_client.models.generate_content.call_args
    assert FIXER_PROMPT_HTML in kwargs["contents"]


def test_ollama_fixer_calls_local_server_and_returns_response(mocker):
    fake_response = mocker.MagicMock()
    fake_response.json.return_value = {"response": "<p>fixed by ollama</p>"}
    fake_response.raise_for_status = mocker.MagicMock()

    mock_get = mocker.patch("scraper.fixing.ollama.requests.get")
    mock_get.return_value = mocker.MagicMock(ok=True)
    mock_post = mocker.patch("scraper.fixing.ollama.requests.post")
    mock_post.return_value = fake_response
    mock_popen = mocker.patch("scraper.fixing.ollama.subprocess.Popen")

    fixer = OllamaFixer(base_url="http://localhost:11434", model="llama3")
    result = fixer.fix_html(FIXER_PROMPT_HTML)

    assert result == "<p>fixed by ollama</p>"
    args, kwargs = mock_post.call_args
    assert args[0] == "http://localhost:11434/api/generate"
    assert kwargs["json"]["model"] == "llama3"
    assert FIXER_PROMPT_HTML in kwargs["json"]["prompt"]
    mock_popen.assert_not_called()


def test_ollama_fixer_starts_server_when_not_running(mocker):
    fake_response = mocker.MagicMock()
    fake_response.json.return_value = {"response": "<p>fixed by ollama</p>"}
    fake_response.raise_for_status = mocker.MagicMock()

    mock_get = mocker.patch("scraper.fixing.ollama.requests.get")
    mock_get.side_effect = [
        mocker.MagicMock(ok=False),
        mocker.MagicMock(ok=True),
    ]
    mock_post = mocker.patch("scraper.fixing.ollama.requests.post")
    mock_post.return_value = fake_response
    mock_popen = mocker.patch("scraper.fixing.ollama.subprocess.Popen")
    mocker.patch("scraper.fixing.ollama.time.sleep")

    fixer = OllamaFixer(base_url="http://localhost:11434", model="llama3")
    result = fixer.fix_html(FIXER_PROMPT_HTML)

    assert result == "<p>fixed by ollama</p>"
    mock_popen.assert_called_once_with(
        ["ollama", "serve"],
        stdout=mocker.ANY,
        stderr=mocker.ANY,
        start_new_session=True,
    )
    mock_post.assert_called_once()


def test_ollama_fixer_raises_when_server_never_becomes_ready(mocker):
    mock_get = mocker.patch("scraper.fixing.ollama.requests.get")
    mock_get.return_value = mocker.MagicMock(ok=False)
    mock_post = mocker.patch("scraper.fixing.ollama.requests.post")
    mocker.patch("scraper.fixing.ollama.subprocess.Popen")

    monotonic_values = iter([0, 1, 100])
    mocker.patch("scraper.fixing.ollama.time.monotonic", side_effect=lambda: next(monotonic_values))
    mocker.patch("scraper.fixing.ollama.time.sleep")

    fixer = OllamaFixer(base_url="http://localhost:11434", model="llama3", startup_timeout=15.0)

    with pytest.raises(RuntimeError):
        fixer.fix_html(FIXER_PROMPT_HTML)

    mock_post.assert_not_called()


def test_gemini_fixer_logs_input_and_output_sizes(mocker, caplog):
    fake_response = mocker.MagicMock()
    fake_response.text = "<p>fixed html</p>"

    fake_client_cls = mocker.patch("scraper.fixing.gemini.genai.Client")
    fake_client_cls.return_value.models.generate_content.return_value = fake_response

    fixer = GeminiFixer(api_key="key-123")
    with caplog.at_level("INFO"):
        fixer.fix_html(FIXER_PROMPT_HTML)

    assert any("input size" in record.message for record in caplog.records)
    assert any("output size" in record.message for record in caplog.records)


def test_openai_fixer_calls_api_and_returns_content(mocker):
    fake_message = mocker.MagicMock()
    fake_message.content = "<p>fixed by openai</p>"
    fake_choice = mocker.MagicMock()
    fake_choice.message = fake_message
    fake_response = mocker.MagicMock()
    fake_response.choices = [fake_choice]

    fake_openai_cls = mocker.patch("scraper.fixing.openai_fixer.OpenAI")
    fake_client = fake_openai_cls.return_value
    fake_client.chat.completions.create.return_value = fake_response

    fixer = OpenAIFixer(api_key="key-456")
    result = fixer.fix_html(FIXER_PROMPT_HTML)

    assert result == "<p>fixed by openai</p>"
    fake_openai_cls.assert_called_once_with(api_key="key-456")


def test_openai_fixer_logs_input_and_output_sizes(mocker, caplog):
    fake_message = mocker.MagicMock()
    fake_message.content = "<p>fixed by openai</p>"
    fake_choice = mocker.MagicMock()
    fake_choice.message = fake_message
    fake_response = mocker.MagicMock()
    fake_response.choices = [fake_choice]

    fake_openai_cls = mocker.patch("scraper.fixing.openai_fixer.OpenAI")
    fake_openai_cls.return_value.chat.completions.create.return_value = fake_response

    fixer = OpenAIFixer(api_key="key-456")
    with caplog.at_level("INFO"):
        fixer.fix_html(FIXER_PROMPT_HTML)

    assert any("input size" in record.message for record in caplog.records)
    assert any("output size" in record.message for record in caplog.records)


def test_all_fixers_implement_content_fixer_interface():
    assert issubclass(GeminiFixer, ContentFixer)
    assert issubclass(OllamaFixer, ContentFixer)
    assert issubclass(OpenAIFixer, ContentFixer)


def test_get_fixer_selects_gemini(mocker):
    mocker.patch("scraper.fixing.gemini.genai.Client")
    settings = AISettings(provider="gemini", gemini_api_key="k", gemini_model="gemini-2.0-flash")
    fixer = get_fixer(settings)
    assert isinstance(fixer, GeminiFixer)
    assert fixer.model == "gemini-2.0-flash"


def test_get_fixer_selects_ollama():
    settings = AISettings(provider="ollama", ollama_base_url="http://localhost:11434", ollama_model="llama3")
    fixer = get_fixer(settings)
    assert isinstance(fixer, OllamaFixer)
    assert fixer.base_url == "http://localhost:11434"
    assert fixer.model == "llama3"


def test_get_fixer_selects_openai(mocker):
    mocker.patch("scraper.fixing.openai_fixer.OpenAI")
    settings = AISettings(provider="openai", openai_api_key="k", openai_model="gpt-4o")
    fixer = get_fixer(settings)
    assert isinstance(fixer, OpenAIFixer)
    assert fixer.model == "gpt-4o"


def test_get_fixer_ignores_inactive_provider_fields(mocker):
    mocker.patch("scraper.fixing.openai_fixer.OpenAI")
    settings = AISettings(
        provider="openai",
        openai_api_key="k",
        openai_model="gpt-4o",
        gemini_api_key="should-be-ignored",
        ollama_model="should-be-ignored",
    )
    fixer = get_fixer(settings)
    assert isinstance(fixer, OpenAIFixer)
    assert fixer.model == "gpt-4o"
