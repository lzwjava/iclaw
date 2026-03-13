import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CONFIG_PATH = path.join(__dirname, '../public/config.json');
const GITHUB_CLIENT_ID = "01ab8ac9400c4e429b23"; // VSCode's client ID

async function getDeviceCode() {
    const resp = await fetch("https://github.com/login/device/code", {
        method: "POST",
        headers: { "Accept": "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({
            client_id: GITHUB_CLIENT_ID,
            scope: "read:user"
        })
    });
    const data = await resp.json();
    console.log(`\n➡️  Visit: ${data.verification_uri}`);
    console.log(`➡️  Enter code: ${data.user_code}\n`);
    return data;
}

async function pollForAccessToken(deviceCode, interval = 5) {
    while (true) {
        await new Promise(resolve => setTimeout(resolve, interval * 1000));
        const resp = await fetch("https://github.com/login/oauth/access_token", {
            method: "POST",
            headers: { "Accept": "application/json", "Content-Type": "application/json" },
            body: JSON.stringify({
                client_id: GITHUB_CLIENT_ID,
                device_code: deviceCode,
                grant_type: "urn:ietf:params:oauth:grant-type:device_code"
            })
        });
        const data = await resp.json();

        if (data.access_token) {
            console.log("✅ GitHub OAuth token obtained.");
            return data.access_token;
        } else if (data.error === "authorization_pending") {
            process.stdout.write("⏳ Waiting for user authorization...\r");
        } else if (data.error === "slow_down") {
            interval += 5;
        } else if (data.error === "expired_token") {
            throw new Error("Device code expired. Please restart.");
        } else {
            throw new Error(`OAuth error: ${JSON.stringify(data)}`);
        }
    }
}

async function main() {
    try {
        const deviceData = await getDeviceCode();
        const githubToken = await pollForAccessToken(deviceData.device_code, deviceData.interval);

        const config = {
            github_token: githubToken
        };

        fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2));
        console.log(`\n✅ Saved GitHub token to ${CONFIG_PATH}`);
        console.log("🚀 Now you can run 'npm run dev' and the web app will use this token.");
    } catch (error) {
        console.error("\n❌ Error:", error.message);
        process.exit(1);
    }
}

main();
