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
import functools
import random


load_dotenv()
IS_HEADLESS = True

def profile_worker(debug_port=None, user_data_dir="", page_worker_func=None, title=None, code=None):  # Removed async
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
            page_worker_func(page, title=title, code=code) 

        # Terminate the Chrome process
        #wait for some time
        process.terminate()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def retry(max_attempts=3, delay=1, backoff=2, jitter=True):
    """
    Retry decorator with exponential backoff and optional jitter.
    
    Args:
        max_attempts (int): Maximum number of retry attempts
        delay (float): Initial delay between retries in seconds
        backoff (float): Multiplier for delay after each attempt
        jitter (bool): Add random jitter to prevent thundering herd
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        print(f"Function {func.__name__} failed after {max_attempts} attempts")
                        break
                    
                    wait_time = delay * (backoff ** attempt)
                    if jitter:
                        wait_time += random.uniform(0, wait_time * 0.1)
                    
                    print(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
                    print(f"Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
            
            return False  # Return False on final failure
        return wrapper
    return decorator

def main(title="ketchup sucks", code="aid"):
    """
    Main function to start the Chrome browser with the specified user data directory and debug port.
    """
    
    # we first need to gen the outline script
    # i'll just hardcode the port and user data dir for now since its serial part,
    # but you can change it later whatever is avaiable profile
    # TODO: make it detect avaialble profile, throw error if none and instruct user to create one
    
    # Add the current directory to Python path to ensure imports work
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    from get_outline import get_outline
    
    # Create a retryable version of profile_worker, use the profiler worker func decorated with retry
    outline_worker = retry(max_attempts=3, delay=2)(profile_worker)
    
    with ThreadPoolExecutor(max_workers=15) as executor:
        future1 = executor.submit(outline_worker, debug_port=9223, user_data_dir="scytherkalachuchib", page_worker_func=get_outline, title=title, code=code)

        # Wait for completion
        result1 = future1.result()
        if result1:
            print(f"Worker completed successfully")
        else:
            print(f"Worker failed after all retry attempts")
            
    # at this point, the outline is ready, we 

# Example usage
if __name__ == "__main__":
    main()


