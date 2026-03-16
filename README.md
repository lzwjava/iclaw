# iclaw

[中文](./README_CN.md)

A minimal [openclaw](https://github.com/lzwjava/openclaw) implementation for enterprise-constrained environments. iclaw is a lightweight terminal REPL that provides AI-assisted coding via GitHub Copilot, designed to work where full-featured tools are blocked or restricted — no browser extensions, no IDE plugins, just a plain Python CLI.

## Features

- **Multi-turn conversations** with GitHub Copilot in your terminal.
- **Native Tool Calling**: The model can autonomously invoke web search, execute shell commands, and edit files.
- **Multiple Search Providers**: DuckDuckGo (default), Startpage, Bing, and Tavily.
- **GitHub OAuth device flow** authentication.
- **Automatic token refresh** during sessions.
- **Modern Default**: Uses GPT-5.2 as the default model.

## Todo

- Support the `/log` command to display and copy the logs to the clipboard.
- Test iclaw in enterprise environments.
- Consult with friends at large corporations to better understand enterprise environment constraints.

## Installation

```bash
git clone https://github.com/lzwjava/iclaw
cd iclaw
pip install -e .
```

## Usage

1. **Start the REPL**:
   ```bash
   iclaw
   ```

2. **Authenticate with GitHub** (on first run):
   ```
   /model_provider
   ```
   Select `copilot`, then follow the GitHub device authorization flow. Your token is saved to `~/.config/iclaw/config.json`.

### CLI Commands
- `/model_provider`: Select and authenticate with the model provider.
- `/model`: View and switch between available models.
- `/search_provider`: View and switch web search providers (default: DuckDuckGo).
- `/copy`: Copy the last response to your clipboard.
- `/help`: Show available commands.
- `.exit`: Quit the REPL.

## Native Tool Calling

The model has access to three tools it can invoke autonomously:

- **web_search**: Search the web for current information using your selected provider.
- **exec**: Execute shell commands with a 30-second timeout.
- **edit**: Apply unified diff patches to create or modify files.

## Search Providers

Switch providers during a session with `/search_provider`:

| Provider | API Key Required | Notes |
|----------|-----------------|-------|
| DuckDuckGo | No | Default provider |
| Startpage | No | Privacy-focused |
| Bing | No | Microsoft Bing |
| Tavily | Yes (`TAVILY_API_KEY`) | AI-native search API |

---

## Development

### Running Tests
We use `unittest` and `coverage` for testing.
```bash
python3 -m coverage run -m unittest discover tests
python3 -m coverage report -m
```

### Project Structure
```
iclaw/
├── commands/     # Modular CLI command handlers
├── tools/        # Tool implementations (edit)
├── main.py       # Core REPL loop and tool definitions
├── github_api.py # GitHub/Copilot API communication
├── web_search.py # Search providers and content extraction
├── exec_tool.py  # Shell command execution tool
└── login.py      # OAuth device flow logic

tests/            # Unit tests
integration_tests/# Network-dependent integration tests
```
