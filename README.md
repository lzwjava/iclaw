# Copilot CLI

An interactive terminal REPL for chatting with GitHub Copilot, built with Node.js.

## Features

- Multi-turn conversations with GitHub Copilot in your terminal
- GitHub OAuth device flow authentication
- Automatic Copilot token refresh during session
- GPT-4o model

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Authenticate with GitHub:
   ```bash
   npm run login
   ```
   This runs the GitHub device authorization flow and saves your token to `public/config.json`.

3. Start the REPL:
   ```bash
   npm start
   ```

## Usage

```
> What is a closure in JavaScript?

GitHub Copilot: A closure is ...

> Can you give me an example?

GitHub Copilot: Sure! Here's an example ...
```

Type `.exit` or press `Ctrl+C` to quit.

## Available Scripts

- `npm start` - Start the interactive CLI
- `npm run login` - Authenticate with GitHub via device flow
- `npm run lint` - Run ESLint

## Project Structure

```
scripts/
└── login.js        # CLI login utility

src/
└── cli.js          # Interactive REPL

public/
└── config.json     # Generated token store (gitignored)
```
