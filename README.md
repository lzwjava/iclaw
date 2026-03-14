# leanclaw

An interactive terminal REPL for chatting with GitHub Copilot, built with Python.

## Features

- **Multi-turn conversations** with GitHub Copilot in your terminal.
- **Native Tool Calling**: Automatically triggers web searches when real-time information is needed.
- **Customizable**: Select search providers and models during the session.
- **GitHub OAuth device flow** authentication.
- **Automatic token refresh** during sessions.
- **Modern Default**: Uses GPT-5.2 as the default model.

## Installation

```bash
git clone https://github.com/lzwjava/leanclaw
cd leanclaw
pip install -e .
```

## Usage

1. **Authenticate with GitHub** (once):
   ```bash
   leanclaw-login
   ```
   This runs the GitHub device authorization flow and saves your token to `~/.config/leanclaw/config.json`.

2. **Start the REPL**:
   ```bash
   leanclaw
   ```

### CLI Commands
- `/login`: Authenticate with GitHub.
- `/model`: View and switch between available models.
- `/search_provider`: View and switch web search providers (default: DuckDuckGo).
- `/copy`: Copy the last response to your clipboard.
- `/help`: Show available commands.
- `.exit`: Quit the REPL.

## Web Search (Native Tool Calling)
The agent is equipped with a `web_search` tool. When you ask about recent events or real-time data, the model will autonomously invoke the tool, fetch content, and provide an answer based on live results.

---

[中文说明 (README_CN.md)](README_CN.md)

## Development

### Running Tests
We use `unittest` and `coverage` for testing.
```bash
python3 -m coverage run -m unittest discover tests
python3 -m coverage report -m
```

### Project Structure
```
leanclaw/
├── commands/     # Modular CLI command handlers
├── main.py       # Core REPL loop and tool definitions
├── github_api.py # GitHub/Copilot API communication
├── web_search.py # DuckDuckGo search and extraction logic
└── login.py      # OAuth device flow logic

tests/            # Unit tests
integration_tests/# Network-dependent integration tests
```
