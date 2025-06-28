# this is just playwright code 


def get_outline(page, title=None, code=None):  # Removed async
    """Navigate to ChatGPT website using the provided page object"""
    
    if title is None:
        raise ValueError("Title must be provided")
    if code is None:
        raise ValueError("Code must be provided")
    import os
    this_script_path = os.path.dirname(os.path.abspath(__file__))
    try:
        # Navigate to ChatGPT
        print("Navigating to ChatGPT...")
        page.goto("https://chatgpt.com", wait_until="networkidle")  # Removed await
        
        # Wait for the page to fully load
        page.wait_for_load_state("networkidle")  # Removed await
        
        print("hello im in chatgpt")

        # read a file named script1_outline.txt and store in a string variable named outline
        outline_file_path = os.path.join(os.path.dirname(__file__), "script1_outline.txt")
        if not os.path.exists(outline_file_path):
            raise FileNotFoundError(f"Outline file '{outline_file_path}' not found.")
        with open(outline_file_path, 'r') as file:
            outline = file.read()
        
        
        print("typing the outline and title into the chat input")
        page.fill("p", outline + "\n" + title)

        print("submitting the outline and title")
        page.keyboard.press("Enter")  # Removed await

        # Wait for ChatGPT to finish generating by waiting for UI indicators
        print("Waiting for ChatGPT to finish generating...")
        try:
            # Wait for stop button to appear first (generation started)
            page.wait_for_selector("[data-testid='stop-button']", timeout=10000)
            print("Generation started, waiting for completion...")
            # Then wait for it to disappear (generation finished)
            page.wait_for_selector("[data-testid='stop-button']", state="hidden", timeout=120000)
            print("Generation completed!")
        except:
            print("Stop button not found, trying copy button...")
            # Fallback: wait for copy button to appear
            page.wait_for_selector("[data-testid='copy-turn-action-button']", timeout=120000)
            print("Copy button appeared - generation likely complete!")

        # go up one level and find the project folder
        project_folder = os.path.join(this_script_path, "..", "projects")
        if not os.path.exists(project_folder):
            raise FileNotFoundError(f"Project folder '{project_folder}' not found.")
        # find the folder that starts with the code argument
        project_folders = [f for f in os.listdir(project_folder) if f.startswith(code)]
        if not project_folders:
            raise FileNotFoundError(f"No project folder found starting with code '{code}'.")
        project_path = os.path.join(project_folder, project_folders[0])
        print(f"Project folder found: {project_path}")        

        # do a screenshot of the page
        screenshot_path = os.path.join(project_path, "chatgpt_screenshot.png")
        print(f"Taking screenshot and saving to {screenshot_path}")
        page.screenshot(path=screenshot_path, full_page=True)  # Removed await
        print("clickin the copy")
        page.click("button:has-text('Copy')")  # Removed await
    
        # whatever is in the clipboard, we store it in a string var
        clipboard_content = page.evaluate("navigator.clipboard.readText()")  # Removed await
        print(f"Clipboard content: {clipboard_content}")
    
        return True

    except Exception as e:
        print(f"Error navigating to ChatGPT: {e}")
        return False