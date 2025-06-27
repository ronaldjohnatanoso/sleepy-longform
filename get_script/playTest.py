# This script is to run one profile of chrome with the given user data dir and debug port
# run the sh script to open the browser and connect to it
# feature is in function but a the main function we just call the function with default values
import subprocess
import asyncio
from playwright.async_api import async_playwright
import os

IS_HEADLESS = True  # Set to True if you want to run Chrome in headless mode

async def start_chrome_and_take_screenshot(user_data_dir="scytherkalachuchi", debug_port="9222"):
    """Start Chrome and take screenshot using simple approach"""
    
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    start_sh_path = os.path.join(script_dir, "start.sh")
    
    print(f"Starting Chrome with profile: {user_data_dir}, port: {debug_port}")
    
    try:
        # Make sure start.sh is executable
        subprocess.run(["chmod", "+x", start_sh_path], check=True)
        
        # Start Chrome in background with headless=true
        process = subprocess.Popen([start_sh_path, user_data_dir, debug_port, str(IS_HEADLESS).lower()],)
        
        # Give Chrome time to start up
        print("Waiting for Chrome to start...")
        await asyncio.sleep(8)  # Give it a bit more time
        
        # Connect and take screenshot
        async with async_playwright() as p:
            # Connect to the existing Chrome instance
            browser = await p.chromium.connect_over_cdp(f"http://localhost:{debug_port}")
            
            # Get or create a page
            contexts = browser.contexts
            if contexts:
                context = contexts[0]
            else:
                context = await browser.new_context()
            
            pages = context.pages
            if pages:
                page = pages[0]
            else:
                page = await context.new_page()
            
            # Navigate to bot detection site
            print("Navigating to https://bot.sannysoft.com/")
            await page.goto("https://bot.sannysoft.com/")
            
            # Wait for page to load completely
            await page.wait_for_load_state("networkidle")
            
            # Take full page screenshot
            screenshot_path = f"bot_sannysoft_screenshot_{user_data_dir}_{debug_port}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot saved as: {screenshot_path}")
            
            print(f"Page title: {await page.title()}")
            
            # Don't close browser, just disconnect
            print("Screenshot completed successfully!")
        
        # Terminate the Chrome process
        # process.terminate()
        process.wait()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

async def main():
    """Main function with default values"""
    await start_chrome_and_take_screenshot()

if __name__ == "__main__":
    asyncio.run(main())