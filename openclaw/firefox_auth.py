import asyncio
from playwright.async_api import async_playwright
import os

async def run_firefox_auth():
    print("--- GITHUB BROWSER AUTOMATION (FIREFOX) ---")
    
    # Path to your CLONED Firefox profile
    user_data_dir = "/tmp/firefox_clone"
    
    async with async_playwright() as p:
        print(f"Launching Firefox with profile: {user_data_dir}...")
        
        # We use launch_persistent_context to utilize your existing session/cookies
        try:
            context = await p.firefox.launch_persistent_context(
                user_data_dir,
                headless=True,
                # Some profiles have dynamic locks, we might need to handle those
            )
        except Exception as e:
            print(f"FAILED TO LAUNCH WITH PROFILE: {e}")
            print("Trying a temporary copy of the profile...")
            # If the profile is "in use" (locked), we'd need to copy it, but let's try direct first.
            return

        page = await context.new_page()
        
        try:
            print("Navigating to https://github.com/login/device...")
            await page.goto("https://github.com/login/device", wait_until="load", timeout=60000)
            
            print(f"Current URL: {page.url}")
            print(f"Page Title: {await page.title()}")
            await page.screenshot(path="firefox_status.png")

            # Check if login is needed
            if "login" in page.url and "device" not in page.url:
                print("!! Still on login page. Firefox profile might be locked or session expired.")
                # We could attempt to autofill here if Playwright can see the saved credentials
            else:
                print("Found device code page! Entering code...")
                await page.wait_for_selector("#user-code", state="visible", timeout=10000)
                await page.fill("#user-code", "837A-E26D")
                await page.keyboard.press("Enter")
                
                await asyncio.sleep(5)
                await page.screenshot(path="firefox_after_code.png")
                
                # Check for Authorize
                auth_btn = page.locator('button:has-text("Authorize"), button:has-text("Continue")')
                if await auth_btn.is_visible():
                    print("Clicking Authorize...")
                    await auth_btn.click()
                    await asyncio.sleep(5)
                    await page.screenshot(path="firefox_final.png")
                
                print("Final URL:", page.url)
                if "success" in page.url.lower():
                    print("SUCCESS: Device linked via Firefox session!")
                else:
                    print("Verification pending or failed.")

        except Exception as e:
            print(f"ERROR: {e}")
            await page.screenshot(path="firefox_error.png")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(run_firefox_auth())
