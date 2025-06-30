# the main is the entry point
# it will call outline first

import subprocess
import os
from pathlib import Path
from dotenv import load_dotenv
import threading
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor, as_completed
import subprocess
import time
from playwright.sync_api import sync_playwright  # Changed from async_playwright
import sys
import json


load_dotenv()
IS_HEADLESS = True

def browser_init(debug_port=None, user_data_dir="", page_worker_func=None, **kwargs):
    """
    open the browser with debug port and user data directory
    
    Dependent scripts:
    - start.sh: Script to start Chrome with the specified user data directory and debug port.
    
    Args:
        debug_port (int): Port for remote debugging
        user_data_dir (str): Chrome user data directory
        page_worker_func (function): Function to perform actions on the page after it is opened, this function takes a page argument.
        **kwargs: Additional keyword arguments to pass to the page_worker_func
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
            result = page_worker_func(page, **kwargs)
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
                # print(f"Cleaned up {singleton_file}")
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
        try:
            # Use lsof to check if port is in use
            result = subprocess.run(["lsof", "-i", f":{port}"], 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL, 
                                  timeout=5)
            # If lsof returns 0, the port is in use
            # If lsof returns 1, the port is available
            if result.returncode != 0:
                print(f"Port {port} is available")
                return port
            else:
                print(f"Port {port} is in use, trying next port")
        except subprocess.TimeoutExpired:
            print(f"Timeout checking port {port}, assuming it's available")
            return port
        except Exception as e:
            print(f"Error checking port {port}: {e}, assuming it's available")
            return port
    
    print(f"Could not find available port after {max_attempts} attempts")
    return None

def update_section_status(section_status_file, section_number, status=None, failures_num=None, worker_name=None):
    """Update section status in the JSON file"""
    try:
        with open(section_status_file, 'r', encoding='utf-8') as f:
            section_status = json.load(f)
        
        for section in section_status:
            if section['section_number'] == section_number:
                if status is not None:
                    section['status'] = status
                if failures_num is not None:
                    section['failures_num'] = failures_num
                if worker_name is not None:
                    section['worker_name'] = worker_name
                break
        
        with open(section_status_file, 'w', encoding='utf-8') as f:
            json.dump(section_status, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error updating section status: {e}")

def log_error(project_path, section_number, worker_name, error_message):
    """Log error to a text file in the project folder"""
    log_file = os.path.join(project_path, "errors.log")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] Section {section_number}, Worker {worker_name}: {error_message}\n")

def worker_task(section_number, profile_name, debug_port, page_worker_func, project_path, section_status_file, **kwargs):
    """Worker task to process a single section"""
    try:
        print(f"Worker {profile_name} processing section {section_number} on port {debug_port}")
        
        # Update status to in progress with worker name
        update_section_status(section_status_file, section_number, status="in_progress", worker_name=profile_name)
        
        # Call browser_init with the section_number in kwargs
        result = browser_init(
            debug_port=debug_port,
            user_data_dir=profile_name,
            page_worker_func=page_worker_func,
            section_number=section_number,
            **kwargs
        )
        
        if result:
            # Success - mark as done with worker name
            update_section_status(section_status_file, section_number, status="done", worker_name=profile_name)
            print(f"Section {section_number} completed successfully by worker {profile_name}")
            return {"section_number": section_number, "success": True, "worker": profile_name}
        else:
            # Failed - increment failures but keep worker name
            raise Exception("Worker function returned False")
            
    except Exception as e:
        error_msg = str(e)
        print(f"Error in section {section_number} with worker {profile_name}: {error_msg}")
        log_error(project_path, section_number, profile_name, error_msg)
        # Update with failure but keep worker name for tracking
        update_section_status(section_status_file, section_number, worker_name=profile_name)
        return {"section_number": section_number, "success": False, "worker": profile_name, "error": error_msg}

def check_section_status(project_path, total_sections):
    """
    Check the status of sections in the project
    
    Returns:
        tuple: (all_done, existing_status, pending_sections)
        - all_done: bool, True if all sections are done
        - existing_status: list, existing section status data or None
        - pending_sections: list, sections that still need to be processed
    """
    section_status_file = os.path.join(project_path, "section_status.json")
    
    if not os.path.exists(section_status_file):
        # No existing status file
        return False, None, list(range(1, total_sections + 1))
    
    try:
        with open(section_status_file, 'r', encoding='utf-8') as f:
            existing_status = json.load(f)
        
        # Check if we have the right number of sections
        if len(existing_status) != total_sections:
            print(f"Warning: Existing status has {len(existing_status)} sections, but expected {total_sections}")
            # If the numbers don't match, we'll need to handle this case
            # For now, let's create missing sections
            existing_section_numbers = {s['section_number'] for s in existing_status}
            for i in range(1, total_sections + 1):
                if i not in existing_section_numbers:
                    existing_status.append({
                        "section_number": i,
                        "failures_num": 0,
                        "status": "pending",
                        "worker_name": None
                    })
            
            # Sort by section number
            existing_status.sort(key=lambda x: x['section_number'])
        
        # Check completion status
        done_sections = [s for s in existing_status if s['status'] == 'done']
        pending_sections = [s['section_number'] for s in existing_status 
                          if s['status'] in ['pending', 'failed']]
        in_progress_sections = [s['section_number'] for s in existing_status 
                              if s['status'] == 'in_progress']
        
        # Treat in_progress as pending (they might have been interrupted)
        pending_sections.extend(in_progress_sections)
        
        all_done = len(done_sections) == total_sections
        
        print(f"Existing status: {len(done_sections)}/{total_sections} sections done")
        if pending_sections:
            print(f"Pending sections: {sorted(pending_sections)}")
        
        return all_done, existing_status, pending_sections
        
    except Exception as e:
        print(f"Error reading existing section status: {e}")
        print("Will create new status file")
        return False, None, list(range(1, total_sections + 1))

def parallel_sections(page_worker_func, sections, title=None, code=None):
    """    Run workers in parallel for each section.
    Args:
        page_worker_func (page worker func that accepts a page arg): the running of the browser is inside this func
        sections (int): number of total sections, will be made to a list inside this function, start with 1
        title (str, optional): full title of the project.
        code (str, optional): prefix code for easier identification of the project folder.
    """
    
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
    
    # Check existing section status
    all_done, existing_status, pending_sections = check_section_status(project_path, sections)
    
    if all_done:
        print("✓ All sections are already completed! Skipping parallel processing.")
        return
    
    if not pending_sections:
        print("✓ No pending sections found! All work is complete.")
        return
    
    print(f"Processing {len(pending_sections)} pending sections...")
    
    # Use existing status or create new one
    if existing_status:
        section_status = existing_status
        # Reset any in_progress sections to pending
        for section in section_status:
            if section['status'] == 'in_progress':
                section['status'] = 'pending'
                section['worker_name'] = None
    else:
        # Create new section status
        section_status = []
        for i in range(1, sections + 1):
            section_status.append({
                "section_number": i,
                "failures_num": 0,
                "status": "pending",
                "worker_name": None
            })
    
    # Save/update the section status file
    section_status_file = os.path.join(project_path, "section_status.json")
    with open(section_status_file, 'w', encoding='utf-8') as f:
        json.dump(section_status, f, indent=2, ensure_ascii=False)
    print(f"Section status file updated: {section_status_file}")

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

    # Only process pending sections
    max_failures = 3
    
    # Use ProcessPoolExecutor to run workers in parallel
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # Track active futures and their associated section numbers
        future_to_section = {}
        completed_sections = set()
        
        # Submit initial batch of work - only pending sections
        worker_index = 0
        while pending_sections and len(future_to_section) < num_workers:
            section_number = pending_sections.pop(0)
            profile_name = profile_names[worker_index % num_workers]
            
            # Find available port for this worker
            debug_port = find_available_port_from_starting_port(9222 + worker_index)
            if debug_port is None:
                print(f"Could not find available port for worker {worker_index}")
                exit(1)
            
            future = executor.submit(
                worker_task,
                section_number=section_number,
                profile_name=profile_name,
                debug_port=debug_port,
                page_worker_func=page_worker_func,
                project_path=project_path,
                section_status_file=section_status_file,
                title=title,
                code=code
            )
            future_to_section[future] = section_number
            worker_index += 1
        
        # Process completed tasks and submit new ones
        while future_to_section:
            # Wait for at least one task to complete
            for future in as_completed(future_to_section):
                section_number = future_to_section[future]
                
                try:
                    result = future.result()
                    
                    if result['success']:
                        completed_sections.add(section_number)
                        print(f"✓ Section {section_number} completed successfully by {result['worker']}")
                    else:
                        # Handle failure - increment failure count but keep worker name
                        with open(section_status_file, 'r', encoding='utf-8') as f:
                            current_status = json.load(f)
                        
                        for section in current_status:
                            if section['section_number'] == section_number:
                                section['failures_num'] += 1
                                
                                if section['failures_num'] >= max_failures:
                                    # Max failures reached - mark as failed but keep last worker name
                                    update_section_status(section_status_file, section_number, status="failed")
                                    print(f"✗ Section {section_number} failed after {max_failures} attempts (last worker: {result['worker']})")
                                    completed_sections.add(section_number)
                                else:
                                    # Retry - add back to pending sections, reset worker name to None for next attempt
                                    pending_sections.append(section_number)
                                    update_section_status(section_status_file, section_number, status="pending", worker_name=None)
                                    print(f"↻ Section {section_number} failed, retrying (attempt {section['failures_num'] + 1}) - last worker: {result['worker']}")
                                
                                # Update the JSON file
                                with open(section_status_file, 'w', encoding='utf-8') as f:
                                    json.dump(current_status, f, indent=2, ensure_ascii=False)
                                break
                
                except Exception as e:
                    print(f"Exception processing section {section_number}: {e}")
                    log_error(project_path, section_number, "unknown", str(e))
                
                # Remove completed future
                del future_to_section[future]
                
                # Submit new work if available
                if pending_sections:
                    new_section = pending_sections.pop(0)
                    profile_name = profile_names[worker_index % num_workers]
                    
                    debug_port = find_available_port_from_starting_port(9222 + worker_index)
                    if debug_port is None:
                        print(f"Could not find available port for worker {worker_index}")
                        # Put section back in queue
                        pending_sections.insert(0, new_section)
                        break
                    
                    new_future = executor.submit(
                        worker_task,
                        section_number=new_section,
                        profile_name=profile_name,
                        debug_port=debug_port,
                        page_worker_func=page_worker_func,
                        project_path=project_path,
                        section_status_file=section_status_file,
                        title=title,
                        code=code
                    )
                    future_to_section[new_future] = new_section
                    worker_index += 1
                
                # Break from the for loop to check if there are more futures
                break
    
    # Calculate final statistics
    with open(section_status_file, 'r', encoding='utf-8') as f:
        final_status = json.load(f)
    
    done_count = len([s for s in final_status if s['status'] == 'done'])
    failed_count = len([s for s in final_status if s['status'] == 'failed'])
    
    print(f"Processing complete: {done_count}/{sections} sections done, {failed_count} failed")

def main(title="", code=""):
    """
    Main function to start the Chrome browser with the specified user data directory and debug port.
    """
    
    # Add the current directory to Python path to ensure imports work
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # check if the project already has an outline.json file so we can skip the outline generation
    project_folder = os.path.join(current_dir, "..", "projects")
    if not os.path.exists(project_folder):
        raise FileNotFoundError(f"Project folder '{project_folder}' not found.")
    project_folders = [f for f in os.listdir(project_folder) if f.startswith(code)]
    if not project_folders:
        raise FileNotFoundError(f"No project folder found starting with code '{code}'.")
    project_path = os.path.join(project_folder, project_folders[0])     
    outline_file_path = os.path.join(project_path, "outline.json")
    
    if not os.path.exists(outline_file_path):
        print("No outline.json found, generating outline...")
        from get_outline import get_outline
        
        # Simple retry logic with ThreadPoolExecutor
        max_attempts = 3
        delay = 2
        
        with ThreadPoolExecutor(max_workers=15) as executor:
            for attempt in range(max_attempts):
                try:
                    print(f"Attempt {attempt + 1} of {max_attempts}")
                    future1 = executor.submit(browser_init, 
                                            debug_port=9223, 
                                            user_data_dir="scytherkalachuchig", 
                                            page_worker_func=get_outline, 
                                            title=title, 
                                            code=code)
                    
                    # Wait for completion
                    result1 = future1.result()
                    print(f"DEBUG: result1 = {result1}, type = {type(result1)}")
                    
                    if result1:
                        print(f"Outline generation completed successfully")
                        break  # Success, exit the retry loop
                    else:
                        print(f"Outline generation returned False on attempt {attempt + 1}")
                        if attempt < max_attempts - 1:  # Not the last attempt
                            print(f"Retrying in {delay} seconds...")
                            time.sleep(delay)
                            delay *= 2  # Exponential backoff
                        else:
                            print(f"Outline generation failed after all {max_attempts} attempts")
                            return  # Exit if outline generation fails
                            
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed with exception: {e}")
                    if attempt < max_attempts - 1:  # Not the last attempt
                        print(f"Retrying in {delay} seconds...")
                        time.sleep(delay)
                        delay *= 2  # Exponential backoff
                    else:
                        print(f"Outline generation failed after all {max_attempts} attempts")
                        return  # Exit if outline generation fails
    else:
        print("✓ Outline.json found, skipping outline generation")
    
    # At this point, the outline should be ready
    # Now check if we need to process sections
    print("Starting section script generation...")
    from get_section_script import get_section_script
    parallel_sections(
        page_worker_func=get_section_script,
        sections=15,  # Example number of sections
        title=title, 
        code=code
    )


