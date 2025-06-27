# the main is the entry point
# it will call outline first

import subprocess
import os
from pathlib import Path
from dotenv import load_dotenv
import threading
from concurrent.futures import ThreadPoolExecutor
import subprocess
import time
from playwright.sync_api import sync_playwright  # Changed from async_playwright


load_dotenv()
IS_HEADLESS = False

def profile_worker(debug_port=None, user_data_dir="", page_worker_func=None):  # Removed async
    """
    open the browser with debug port and user data directory
    
    Dependent scripts:
    - start.sh: Script to start Chrome with the specified user data directory and debug port.
    
    Args:
        debug_port (int): Port for remote debugging
        user_data_dir (str): Chrome user data directory
        page_worker_func (function): Function to perform actions on the page after it is opened, this function takes a page argument.
    """

    
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    start_sh_path = os.path.join(script_dir, "start.sh")
    
    print(f"Starting Chrome with profile: {user_data_dir}, port: {debug_port}")
    
    try:
        # Make sure start.sh is executable
        subprocess.run(["chmod", "+x", start_sh_path], check=True)
        
        # Start Chrome in background
        process = subprocess.Popen([start_sh_path, user_data_dir, str(debug_port), str(IS_HEADLESS).lower()],)
        
        # Give Chrome time to start up
        print("Waiting for Chrome to start...")
        time.sleep(8)  # Changed from await asyncio.sleep(8)
        
        # Connect using sync API
        with sync_playwright() as p:  # Changed from async with async_playwright()
            # Connect to the existing Chrome instance
            browser = p.chromium.connect_over_cdp(f"http://localhost:{debug_port}")  # Removed await
            
            # Get or create a page
            contexts = browser.contexts
            if contexts:
                context = contexts[0]
            else:
                context = browser.new_context()  # Removed await
            
            pages = context.pages
            if pages:
                page = pages[0]
            else:
                page = context.new_page()  # Removed await
            
            # Once we have the page, we pass it to another module that does the actual work
            page_worker_func(page)  # Removed await

        # Terminate the Chrome process
        # process.terminate()
        process.wait()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """
    Main function to start the Chrome browser with the specified user data directory and debug port.
    """
    
    # we first need to gen the outline script
    # i'll just hardcode the port and user data dir for now since its serial part,
    # but you can change it later whatever is avaiable profile
    # TODO: make it detect avaialble profile, throw error if none and instruct user to create one
    from get_outline import get_outline
    with ThreadPoolExecutor(max_workers=15) as executor:
        future1 = executor.submit(profile_worker, debug_port=9222, user_data_dir="scytherkalachuchi", page_worker_func=get_outline)

        # Wait for completion
        result1 = future1.result()
        print(f"Worker completed with result: {result1}")    

    # we need one worker to generate the outline script
    result = profile_worker(debug_port=debug_port, user_data_dir=user_data_dir)
    
    if result:
        print("Profile worker completed successfully.")
    else:
        print("Profile worker failed.")

# Example usage
if __name__ == "__main__":
    from get_outline import get_outline
    
    # Now this works with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=15) as executor:
        future1 = executor.submit(profile_worker, debug_port=9222, user_data_dir="scytherkalachuchi", page_worker_func=get_outline)

        # Wait for completion
        result1 = future1.result()
        print(f"Worker completed with result: {result1}")


