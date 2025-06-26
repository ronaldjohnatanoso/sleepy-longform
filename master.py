#This script is like the orchestrator that manages the main pipeline
import os 
import argparse
import subprocess
import re
from datetime import datetime

CWD = os.getcwd()

def get_title_from_google_sheets():
    #find the get_title directory
    get_title_dir = os.path.join(CWD, "get_title")
    # Call the only function inside main.py in get_title directory
    from get_title.main import get_title_from_google_sheets
    return get_title_from_google_sheets()

def sanitize_folder_name(title):
    """Convert title to safe folder name"""
    # Remove or replace invalid characters for folder names
    sanitized = re.sub(r'[<>:"/\\|?*]', '', title)  # Remove invalid chars
    sanitized = re.sub(r'\s+', '_', sanitized.strip())  # Replace spaces with underscores
    sanitized = sanitized[:40]  # Shorter limit
    return sanitized

def get_next_project_number():
    """Get the next sequential project number"""
    projects_dir = os.path.join(CWD, "projects")
    
    # Create projects directory if it doesn't exist
    if not os.path.exists(projects_dir):
        os.makedirs(projects_dir)
        return 1
    
    # Find existing project folders and extract numbers
    existing_numbers = []
    for folder in os.listdir(projects_dir):
        if os.path.isdir(os.path.join(projects_dir, folder)):
            # Extract number from folder name (format: a1_, a2_, etc.)
            match = re.match(r'a(\d+)_', folder)
            if match:
                existing_numbers.append(int(match.group(1)))
    
    # Return next number (or 1 if no projects exist)
    return max(existing_numbers) + 1 if existing_numbers else 1

def create_project_folder(title):
    """Create project folder with simple sequential numbering"""
    # Get next project number
    project_num = get_next_project_number()
    
    # Sanitize the title for folder name
    safe_title = sanitize_folder_name(title)
    
    # Create folder name: a1_title, a2_title, etc.
    folder_name = f"a{project_num}_{safe_title}"
    
    # Create full path
    projects_dir = os.path.join(CWD, "projects")
    project_path = os.path.join(projects_dir, folder_name)
    
    # Create the directory
    os.makedirs(project_path, exist_ok=True)
    
    print(f"📁 Created project folder: {folder_name}")
    print(f"📍 Full path: {project_path}")
    
    return project_path, f"a{project_num}"

def main():
    parser = argparse.ArgumentParser(description="Orchestrator for the main pipeline.")
    parser.add_argument('--title', type=str, help='Title to be processed.')
    args = parser.parse_args()
    title = args.title if args.title else "NoCustom"
    
    #if no custom title in arg, we fetch from the googlesheets
    if title == "NoCustom":
        print("No custom title provided, fetching from Google Sheets...")
        title = get_title_from_google_sheets()
        
    if not title:
        print("❌ No title available, exiting...")
        return
        
    print(f"📝 Using title: {title}")
    
    # Create project folder with simple sequential numbering
    project_path, codename = create_project_folder(title)
    
    print(f"🚀 Project codename: {codename}")
    print(f"📂 Ready to process in: {project_path}")
    
    # Use the title and project_path for script generation
    # ... rest of your pipeline code ...

if __name__ == "__main__":
    main()