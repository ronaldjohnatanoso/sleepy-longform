# the main is the entry point
# it will call outline first

import subprocess
import os
from pathlib import Path
from dotenv import load_dotenv
import threading
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor
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

def find_available_port_from_starting_port(starting_port=9222, max_attempts=100):
    """
    Find an available port starting from a given port.
    
    Args:
        starting_port (int): The port to start checking from.
        max_attempts (int): Maximum number of attempts to find an available port.
        
    Returns:
        int: An available port number or None if no port is found.
    """
    
    for i in range(max_attempts):
        port = starting_port + i
        with subprocess.Popen(["lsof", "-i", f":{port}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) as proc:
            if proc.poll() is not None:  # If process is not running, the port is available
                return port
    return None

def parallel_sections(page_worker_func, sections, title=None, code=None):
    """    Run workers in parallel for each section.
    Args:
        page_worker_func (page worker func that accepts a page arg): the running of the browser is inside this func
        sections (int): number of total sections, will be made to a list inside this function, start with 1
        title (str, optional): full title of the project.
        code (str, optional): prefix code for easier identification of the project folder.
    """
    
    # lets make a list of section dict, where an element is section_number, failures_num, and status, start with 1
    section_status = []
    for i in range(1, sections + 1):
        section_status.append({
            "section_number": i,
            "failures_num": 0,
            "status": "pending"
        })
        
    # make that into a json inside the project folder
    # get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # go up one level and find the project folder
    project_folder = os.path.join(current_dir, "..", "projects")
    if not os.path.exists(project_folder):
        raise FileNotFoundError(f"Project folder '{project_folder}' not found.")
    # find the folder that starts with the code argument
    project_folders = [f for f in os.listdir(project_folder) if f.startswith(code)]
    if not project_folders:
        raise FileNotFoundError(f"No project folder found starting with code '{code}'.")
    project_path = os.path.join(project_folder, project_folders[0])
    print(f"Project folder found: {project_path}")
    # create a json file with the section status
    import json
    section_status_file = os.path.join(project_path, "section_status.json")
    with open(section_status_file, 'w', encoding='utf-8') as f:
        json.dump(section_status, f, indent=2, ensure_ascii=False)
    print(f"Section status file created: {section_status_file}")

    """
    Now we can run the workers in parallel, use process pool executor
    using the section list, we need to delegate that section to a worker
    the number of avaible may be less than the number of sections, so we need to handle that
    eventually when a worker finished, this frees it and it can take another section
    we use as_completed to get the results as they come in
    if a process fails, we increment the failures_num for that section
    if failures_num reaches 3, we stop the worker and mark it as failed
    when a section is not picked up yet, it is pending by default
    when it is picked up, it is in progress
    when it is done, either by failing the max times or successfully, it is marked as done in status
    workers numbers aren't just arbitrary, you see in the profiles folder, each profile represent a unique worker
    so we can figure out how many workers we have by counting the profiles in the profiles folder
    if a worker fails for any reason, it would be useful to log the error in a text file in the project folder, specifying the section number and other relevant info like what profile it is of the worker
    """
    # look inside the profiles folder, count the number of profiles
    # make a list where each element is a profile name
    profile_names = []
    profiles_dir = os.path.join(current_dir, "..", "profiles")
    if not os.path.exists(profiles_dir):
        raise FileNotFoundError(f"Profiles directory '{profiles_dir}' not found.")
    for profile in os.listdir(profiles_dir):
        profile_path = os.path.join(profiles_dir, profile)
        if os.path.isdir(profile_path) and not profile.startswith('.'):
            profile_names.append(profile)
    num_workers = len(profile_names)
    print(f"Number of available workers: {num_workers}")
    if num_workers == 0:
        print("No available workers found.")
        exit(1)
    print("profile names", profile_names)
    # the profile names are our workers, if we delegate a work to a worker, we temporarily remove it from the list and add it back when done
    workers = []
    for profile in profile_names:
        worker = {
            "name": profile,
            "status": "idle"
        }
        workers.append(worker)
    print("Workers initialized:", workers)

    """
    we do the process pool parallel stuff, when we delegate the functions to the workers
    we pass the profile worker function ( this starts the browser and intializes the page)
    we also pass the args needed by the page worker based on the following:
    - debug_port: we use the function to find available port starting from 9222, in case returns None, we exit with error
    - user_data_dir: the profile name, which is the worker name
    - page_worker_func: we get this from the argument, this is the function that does the actual work on the page
    - title: the title of the project, this is passed to the page worker function
    - code: the code of the project, this is passed to the page worker function
    """
    
    # use ProcessPoolExecutor to run the workers in parallel


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
    # pass a page worker that accepts a page argument and not the one that starts the browser, the browser starting will be put inside the paralle sections function
    from get_section_script import get_section_script
    parallel_sections(
        func=get_section_script,
        sections=15,  # Example number of sections
        title=title, 
        code=code
    )
    


# Example usage
if __name__ == "__main__":
    main()


