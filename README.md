# Copilot Chat

A web-based chat interface for GitHub Copilot, built with React, TypeScript, and Vite.

## Features

- Chat with GitHub Copilot directly in your browser
- Token-based authentication using GitHub OAuth
- Automatic token refresh to maintain session
- Clean, responsive chat interface
- Support for Copilot's GPT-4o model

## Tech Stack

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **GitHub Copilot API** - AI chat completions

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Login using the CLI (required due to GitHub CORS restrictions):
   ```bash
   npm run login
   ```
   This will:
   - Open a GitHub device authorization flow
   - Save your GitHub token to `public/config.json`

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open your browser to the URL shown (typically `http://localhost:5173`)

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run lint` - Run ESLint
- `npm run preview` - Preview production build
- `npm run login` - Authenticate with GitHub via device flow

## Authentication

This app uses GitHub's OAuth Device Flow for authentication:

1. Run `npm run login` in your terminal
2. Visit the verification URL and enter the provided code
3. Authorize the app on GitHub
4. Your token is saved to `public/config.json`
5. Refresh the web app to start chatting

**Note:** Browser-based login is restricted by GitHub's CORS policies, which is why the CLI login is required.

## API Integration

The app communicates with:
- GitHub OAuth endpoints for device authorization
- GitHub Copilot API for chat completions (`https://api.githubcopilot.com/chat/completions`)
- Automatic token refresh using GitHub's Copilot internal token endpoint

## Project Structure

```
src/
├── App.tsx              # Main chat interface component
├── main.tsx             # Application entry point
├── services/
│   └── auth.ts          # Authentication service
└── assets/              # Static assets

scripts/
└── login.js             # CLI login utility

public/
└── config.json          # Generated config (gitignored)
```

## Development Notes

- Uses React 19's modern features
- Token refresh happens automatically every ~24 minutes
- Session data stored in localStorage
- Copilot tokens include a 1-minute safety buffer before expiry
