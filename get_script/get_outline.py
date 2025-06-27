# this is just playwright code 


def get_outline(page):  # Removed async
    """Navigate to ChatGPT website using the provided page object"""
    
    try:
        # Navigate to ChatGPT
        print("Navigating to ChatGPT...")
        page.goto("https://chatgpt.com", wait_until="networkidle")  # Removed await
        
        # Wait for the page to fully load
        page.wait_for_load_state("networkidle")  # Removed await
        
        print("hello im in chatgpt")
        
        return True
        
    except Exception as e:
        print(f"Error navigating to ChatGPT: {e}")
        return False