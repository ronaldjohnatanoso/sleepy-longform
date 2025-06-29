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
import sys


load_dotenv()
IS_HEADLESS = False

def profile_worker(debug_port=None, user_data_dir="", page_worker_func=None, title=None, code=None):
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
    
    process = None
    result = False
    
      # Ensure process is initialized before using it
    
    try:
        # Make sure start.sh is executable
        subprocess.run(["chmod", "+x", start_sh_path], check=True)
        
        # Start Chrome in background
        process = subprocess.Popen([start_sh_path, user_data_dir, str(debug_port), str(IS_HEADLESS).lower()],)
        
        # Give Chrome time to start up
        print("Waiting for Chrome to start...")
        time.sleep(8)
        
        # Connect using sync API
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(f"http://localhost:{debug_port}")
            
            # Get or create a page
            contexts = browser.contexts
            if contexts:
                context = contexts[0]
                # Grant permissions to existing context
                context.grant_permissions(['clipboard-read', 'clipboard-write'], origin='https://chatgpt.com')
            else:
                # Create new context with permissions already granted
                context = browser.new_context(
                    permissions=['clipboard-read', 'clipboard-write']
                )
            
            pages = context.pages
            if pages:
                page = pages[0]
            else:
                page = context.new_page()
            
            # Once we have the page, we pass it to another module that does the actual work
            result = page_worker_func(page, title=title, code=code)
            print(f"page_worker_func returned: {result}")

    except Exception as e:
        print(f"Error: {e}")
        result = False
        
    finally:
        # Always cleanup Chrome process, regardless of success or failure
        if process and process.poll() is None:
            print("Shutting down Chrome gracefully...")
            try:
                # First try graceful termination
                process.terminate()
                # Wait up to 10 seconds for graceful shutdown
                process.wait(timeout=10)
                print("Chrome shut down gracefully")
            except subprocess.TimeoutExpired:
                print("Chrome didn't shut down gracefully, force killing...")
                # If it doesn't shut down gracefully, force kill
                process.kill()
                process.wait()
            except Exception as cleanup_error:
                print(f"Error during cleanup: {cleanup_error}")
                # Force kill as last resort
                try:
                    process.kill()
                    process.wait()
                except:
                    pass
        
        # Always clean up singleton files after Chrome process is terminated
        # This should happen regardless of graceful or force shutdown
        profiles_dir = os.path.join(script_dir, "..", "profiles")
        user_data_path = os.path.join(profiles_dir, user_data_dir)
        singleton_files = [
            os.path.join(user_data_path, "SingletonLock"),
            os.path.join(user_data_path, "SingletonSocket"),
            os.path.join(user_data_path, "SingletonCookie")
        ]
        for singleton_file in singleton_files:
            try:
                os.remove(singleton_file)
                print(f"Cleaned up {singleton_file}")
            except FileNotFoundError:
                pass  # File doesn't exist, which is fine
            except Exception as e:
                print(f"Failed to clean up {singleton_file}: {e}")
    
    return result

def main(title="ketchup sucks", code="aid"):
    """
    Main function to start the Chrome browser with the specified user data directory and debug port.
    """
    
    # Add the current directory to Python path to ensure imports work
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    from get_outline import get_outline
    
    # Simple retry logic with ThreadPoolExecutor
    max_attempts = 3
    delay = 2
    
    with ThreadPoolExecutor(max_workers=15) as executor:
        for attempt in range(max_attempts):
            try:
                print(f"Attempt {attempt + 1} of {max_attempts}")
                future1 = executor.submit(profile_worker, 
                                        debug_port=9223, 
                                        user_data_dir="scytherkalachuchig", 
                                        page_worker_func=get_outline, 
                                        title=title, 
                                        code=code)
                
                # Wait for completion
                result1 = future1.result()
                print(f"DEBUG: result1 = {result1}, type = {type(result1)}")
                
                if result1:
                    print(f"Worker completed successfully")
                    break  # Success, exit the retry loop
                else:
                    print(f"Worker returned False on attempt {attempt + 1}")
                    if attempt < max_attempts - 1:  # Not the last attempt
                        print(f"Retrying in {delay} seconds...")
                        time.sleep(delay)
                        delay *= 2  # Exponential backoff
                    else:
                        print(f"Worker failed after all {max_attempts} attempts")
                        
            except Exception as e:
                print(f"Attempt {attempt + 1} failed with exception: {e}")
                if attempt < max_attempts - 1:  # Not the last attempt
                    print(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    print(f"Worker failed after all {max_attempts} attempts")
    
    # at this point, the outline is ready

# Example usage
if __name__ == "__main__":
    main()


