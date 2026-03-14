import asyncio
from playwright.async_api import async_playwright
import os

async def run_auth():
    print("--- GITHUB BROWSER AUTOMATION (PYTHON) ---")
    user_data_dir = os.path.expanduser("~/.openclaw/browser-profiles/openclaw")
    
    async with async_playwright() as p:
        # Launching with user data to hope for existing session
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=True
        )
        page = await context.new_page()
        
        try:
            print("Navigating to https://github.com/login/device...")
            await page.goto("https://github.com/login/device", wait_until="networkidle", timeout=60000)
            
            # Check if login is needed
            if "login" in page.url and "device" not in page.url:
                print("!! REDIRECTED TO LOGIN. Looking for session cookies...")
                await page.screenshot(path="github_login_required.png")
                # Even if redirected, we'll try to find the code input just in case
            
            print(f"Current Title: {await page.title()}")
            print(f"Current URL: {page.url}")
            
            # Check for login form items
            if await page.locator('input[name="login"]').is_visible():
                print("!! CONFIRMED: ON LOGIN PAGE. Automation cannot proceed without manual login.")
                return 

            print("Looking for user-code input...")
            # Github uses a single input or multiple. Usually #user-code
            await page.wait_for_selector("#user-code", state="visible", timeout=10000)
            await page.fill("#user-code", "837A-E26D")
            print("Code entered. Submitting...")
            await page.keyboard.press("Enter")
            
            await asyncio.sleep(3)
            await page.screenshot(path="github_after_code.png")
            
            # Look for Authorize button
            auth_btn = page.locator('button:has-text("Authorize"), button:has-text("Continue")')
            if await auth_btn.is_visible():
                print("Clicking Authorize button...")
                await auth_btn.click()
                await asyncio.sleep(5)
                await page.screenshot(path="github_final.png")
            
            print(f"Final URL: {page.url}")
            if "success" in page.url.lower() or "congratulations" in await page.content():
                print("SUCCESS: Device Authorized!")
            else:
                print("Verification may have failed or requires manual login.")
                
        except Exception as e:
            print(f"ERROR: {str(e)}")
            await page.screenshot(path="github_error.png")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(run_auth())
