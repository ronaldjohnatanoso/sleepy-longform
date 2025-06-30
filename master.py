#This script is like the orchestrator that manages the main pipeline
import os 
import argparse
import subprocess
import re
from datetime import datetime
        
import json
CWD = os.path.dirname(os.path.abspath(__file__))

def get_title_from_google_sheets():
    #find the get_title directory
    get_title_dir = os.path.join(CWD, "get_title")
    # Call the only function inside main.py in get_title directory
    from get_title.main import get_title_from_google_sheets
    return get_title_from_google_sheets()


def gen_script(title, code):
    """Generate the script with the given title
    .We just call import the function since its a serial part
    """
    from get_script.main import main as gen_script_main
    gen_script_main(title=title, code=code)

def main():
    parser = argparse.ArgumentParser(description="Orchestrator for the main pipeline.")
    parser.add_argument('--title', type=str, help='Title to be processed.')
    parser.add_argument('--code', type=str, help='Resume a project using a code.', default=None)
    args = parser.parse_args()

    code = args.code
    title = ""

    if code:
        # Validate the code format
        if not re.match(r'^a\d+', code):
            print(f"❌ Invalid code format: {code}. Expected format: a1, a2, etc.")
            return

        print(f"🔍 Looking for project folder starting with code: {code}_")
        project_base = os.path.join(CWD, "projects")
        
        # Find folder starting with code_
        matched_folder = None
        for folder_name in os.listdir(project_base):
            if folder_name.startswith(f"{code}_") and os.path.isdir(os.path.join(project_base, folder_name)):
                matched_folder = os.path.join(project_base, folder_name)
                break
        
        if not matched_folder:
            print(f"❌ No folder found starting with '{code}_' in projects directory.")
            return

        title_file_path = os.path.join(matched_folder, "title.json")
        if not os.path.exists(title_file_path):
            print(f"❌ Title file not found at: {title_file_path}")
            return

        
        with open(title_file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                title = data.get("title", "").strip()
                if not title:
                    print(f"❌ Title key not found or empty in {title_file_path}")
                    return
            except json.JSONDecodeError:
                print(f"❌ Failed to parse JSON in {title_file_path}")
                return
        print(f"Resuming project in: {matched_folder}")


    else:
        # No code provided; use --title or fetch from Google Sheets
        title = args.title if args.title else "NoCustom"

        if title == "NoCustom":
            print("No custom title provided, fetching from Google Sheets...")
            title, code = get_title_from_google_sheets()

        if not title:
            print("❌ No title available, exiting...")
            return

    print(f"📝 Using title: {title}")
    print(f"📝 Using code: {code}")
    
    
    gen_script(title, code)

if __name__ == "__main__":
    main()