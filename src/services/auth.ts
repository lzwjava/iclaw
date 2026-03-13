const GITHUB_CLIENT_ID = '01ab8ac9400c4e429b23'; // VSCode's client ID

export interface CopilotTokenResponse {
  token: string;
  expires_at: number;
  refresh_in: number;
}

export const AuthService = {
  getGithubToken(): string | null {
    return localStorage.getItem('github_token');
  },

  setGithubToken(token: string) {
    localStorage.setItem('github_token', token);
  },

  getCopilotToken(): string | null {
    const tokenData = localStorage.getItem('copilot_token');
    if (!tokenData) return null;
    
    const { token, expires_at } = JSON.parse(tokenData);
    // Add 1 minute buffer (60 seconds) as per instructions Step 3
    if (Date.now() / 1000 > (expires_at - 60)) {
      localStorage.removeItem('copilot_token');
      return null;
    }
    return token;
  },

  async fetchCopilotToken(githubToken: string): Promise<CopilotTokenResponse> {
    const headers = {
      'Authorization': `token ${githubToken}`,
      'Accept': 'application/json',
      'editor-version': 'vscode/1.85.1',
      'editor-plugin-version': 'copilot/1.155.0',
      'user-agent': 'GithubCopilot/1.155.0',
      'Copilot-Integration-Id': 'vscode-chat',
    };

    const response = await fetch('https://api.github.com/copilot_internal/v2/token', {
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to fetch Copilot token. Make sure you have Copilot access.');
    }

    const data = await response.json();
    localStorage.setItem('copilot_token', JSON.stringify({
      token: data.token,
      expires_at: data.expires_at,
    }));
    
    return data;
  },

  async getDeviceCode() {
    const response = await fetch('https://github.com/login/device/code', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        client_id: GITHUB_CLIENT_ID,
        scope: 'read:user',
      }),
    });

    if (!response.ok) throw new Error('Failed to get device code');
    return await response.json();
  },

  async pollForToken(deviceCode: string): Promise<string> {
    const interval = 5000; // Poll every 5 seconds
    
    while (true) {
      const response = await fetch('https://github.com/login/oauth/access_token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          client_id: GITHUB_CLIENT_ID,
          device_code: deviceCode,
          grant_type: 'urn:ietf:params:oauth:grant-type:device_code',
        }),
      });

      const data = await response.json();

      if (data.access_token) {
        return data.access_token;
      }

      if (data.error === 'authorization_pending') {
        await new Promise(resolve => setTimeout(resolve, interval));
        continue;
      }

      throw new Error(data.error_description || 'Token polling failed');
    }
  },

  redirectToGithub() {
    // This will be replaced by the Device Flow UI in App.tsx
  },
};
