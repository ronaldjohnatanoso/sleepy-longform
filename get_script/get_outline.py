# this is just playwright code 


def get_outline(page, title=None, code=None):  # Removed async
    """Navigate to ChatGPT website using the provided page object
        returns True if successful, False otherwise.
    """
    
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

        # pause the page indefinitely
        # page.pause()  # Removed await, this is not needed in sync mode

        # print("submitting the outline and title")
        # page.keyboard.press("Enter")  # Removed await
        
        # click button with selector [data-testid='send-button'] > svg
        print("clicking the send button")
        page.click("[data-testid='send-button'] > svg")  # Removed await

        # Wait for ChatGPT to finish generating by waiting for UI indicators
        print("Waiting for ChatGPT to finish generating...")
        try:
            # Wait for send button to appear first (generation started)
            page.wait_for_selector("[data-testid='send-button'] > svg", timeout=30000)
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


        print("clickin the copy")
        page.click("button:has-text('Copy')")  # Removed await
    
        # do a screen capture of the page
        screenshot_path = os.path.join(project_path, "chatgpt_screenshot.png")
        page.screenshot(path=screenshot_path, full_page=True)  # Removed await
        print(f"Screenshot saved to: {screenshot_path}")
    
        # whatever is in the clipboard, we store it in a string var
        clipboard_content = page.evaluate("() => navigator.clipboard.readText()")  # Removed await
        print(f"Clipboard content: {clipboard_content}")
    
    
        # Clean up the clipboard content by replacing non-breaking spaces with regular spaces
        cleaned_content = clipboard_content.replace('\xa0', ' ')
        
        # parse the clipboard content as JSON
        try:
            import json
            outline_data = json.loads(cleaned_content)  # Use cleaned content instead
            
            # Save the JSON to the project folder
            json_file_path = os.path.join(project_path, "outline.json")
            with open(json_file_path, 'w', encoding='utf-8') as json_file:
                json.dump(outline_data, json_file, indent=2, ensure_ascii=False)
            print(f"Outline saved to: {json_file_path}")
            
            # Add explicit success message here
            print("get_outline function completed successfully, returning True")
            return True
        
        except json.JSONDecodeError as e:
            print(f"Error parsing clipboard content as JSON: {e}")
            print(f"Raw clipboard content type: {type(clipboard_content)}")
            print(f"Raw clipboard content: {repr(clipboard_content)}")
            # Save as raw text if JSON parsing fails
            txt_file_path = os.path.join(project_path, "outline_raw.txt")
            with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
                txt_file.write(str(clipboard_content))
            print(f"Raw content saved to: {txt_file_path}")
            print("get_outline function completed with JSON error, returning True anyway")
            return True

    except Exception as e:
        print(f"Error navigating to ChatGPT: {e}")
        print(f"get_outline function failed with exception, returning False")
        return False