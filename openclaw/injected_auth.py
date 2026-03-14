import asyncio
import json
import os
from playwright.async_api import async_playwright

async def run_injected_auth():
    print("--- GITHUB COOKIE INJECTION AUTHORIZATION ---")
    
    # Load the cookies we just extracted
    try:
        with open("/tmp/github_cookies.json", "r") as f:
            cookies = json.load(f)
    except Exception as e:
        print(f"Error loading cookies: {e}")
        return

    async with async_playwright() as p:
        # Launch Chromium (usually faster/more reliable for headless interaction)
        browser = await p.chromium.launch(headless=True)
        # Create a fresh context to ensure no interference
        context = await browser.new_context()
        
        # INJECT THE COOKIES!
        print(f"Injecting {len(cookies)} cookies...")
        # FORCE session-only for all cookies to avoid timestamp issues
        for cookie in cookies:
            cookie['expires'] = -1
        await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        try:
            print("Navigating to https://github.com/login/device...")
            await page.goto("https://github.com/login/device", wait_until="networkidle", timeout=60000)
            
            print(f"URL: {page.url}")
            print(f"Title: {await page.title()}")
            await page.screenshot(path="injection_result.png")

            if "login" in page.url and "device" not in page.url:
                print("!! Cookies were not accepted or session expired. Login required.")
                # Extra check: print page content snippet
                content = await page.content()
                print("Snippet:", content[:200])
            else:
                print("SUCCESS: Logged in! Entering code 837A-E26D...")
                await page.wait_for_selector("#user-code", state="visible", timeout=10000)
                await page.fill("#user-code", "837A-E26D")
                await page.keyboard.press("Enter")
                
                await asyncio.sleep(5)
                
                # Check for Authorize button
                auth_btn = page.locator('button:has-text("Authorize"), button:has-text("Continue")')
                if await auth_btn.is_visible():
                    print("Clicking Authorize button...")
                    await auth_btn.click()
                    await asyncio.sleep(5)
                
                final_url = page.url
                print(f"Final URL: {final_url}")
                await page.screenshot(path="injection_final.png")
                
                if "success" in final_url.lower() or "congratulations" in await page.content():
                    print("TASK COMPLETE: GitHub Device Authorized!")
                else:
                    print("Verification result uncertain. Check injection_final.png")

        except Exception as e:
            print(f"ERROR during automation: {e}")
            await page.screenshot(path="injection_error.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_injected_auth())
