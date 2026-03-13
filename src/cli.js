#!/usr/bin/env node
import readline from 'readline'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const CONFIG_PATH = path.join(__dirname, '../public/config.json')

function loadGithubToken() {
  if (!fs.existsSync(CONFIG_PATH)) {
    console.error('No token found. Run `npm run login` first.')
    process.exit(1)
  }
  const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'))
  if (!config.github_token) {
    console.error('Invalid config: missing github_token. Run `npm run login` first.')
    process.exit(1)
  }
  return config.github_token
}

async function getCopilotToken(githubToken) {
  const resp = await fetch('https://api.github.com/copilot_internal/v2/token', {
    headers: {
      Authorization: `Bearer ${githubToken}`,
      'Editor-Version': 'vscode/1.85.0',
      'Editor-Plugin-Version': 'copilot/1.155.0',
      'User-Agent': 'GithubCopilot/1.155.0',
    },
  })
  if (!resp.ok) {
    throw new Error(`Failed to get Copilot token: ${resp.status} ${resp.statusText}`)
  }
  const data = await resp.json()
  return data.token
}

async function chat(messages, copilotToken) {
  const resp = await fetch('https://api.githubcopilot.com/chat/completions', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${copilotToken}`,
      'Content-Type': 'application/json',
      'Editor-Version': 'vscode/1.85.0',
      'Editor-Plugin-Version': 'copilot/1.155.0',
      'User-Agent': 'GithubCopilot/1.155.0',
      'Copilot-Integration-Id': 'vscode-chat',
    },
    body: JSON.stringify({
      model: 'gpt-4o',
      messages,
      stream: false,
    }),
  })
  if (!resp.ok) {
    const body = await resp.text()
    throw new Error(`Chat API error: ${resp.status} ${resp.statusText}\n${body}`)
  }
  const data = await resp.json()
  return data.choices[0].message.content
}

async function main() {
  const githubToken = loadGithubToken()

  console.log('Connecting to GitHub Copilot...')
  let copilotToken = await getCopilotToken(githubToken)
  let tokenExpiry = Date.now() + 24 * 60 * 1000 // refresh ~every 24 min

  const messages = []

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    prompt: '> ',
  })

  console.log('GitHub Copilot CLI ready. Type your message or .exit to quit.\n')
  rl.prompt()

  rl.on('line', async (line) => {
    const input = line.trim()
    if (!input) {
      rl.prompt()
      return
    }
    if (input === '.exit') {
      console.log('Goodbye!')
      process.exit(0)
    }

    rl.pause()

    try {
      // Refresh token if near expiry
      if (Date.now() >= tokenExpiry) {
        copilotToken = await getCopilotToken(githubToken)
        tokenExpiry = Date.now() + 24 * 60 * 1000
      }

      messages.push({ role: 'user', content: input })
      const reply = await chat(messages, copilotToken)
      messages.push({ role: 'assistant', content: reply })

      console.log(`\nGitHub Copilot: ${reply}\n`)
    } catch (err) {
      console.error(`Error: ${err.message}`)
    }

    rl.resume()
    rl.prompt()
  })

  rl.on('close', () => {
    console.log('\nGoodbye!')
    process.exit(0)
  })
}

main()
