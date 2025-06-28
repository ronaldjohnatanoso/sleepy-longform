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


def gen_script(title, code):
    """Generate the script with the given title
    .We just call import the function since its a serial part
    """
    from get_script.main import main as gen_script_main
    gen_script_main(title=title, code=code)

def main():
    parser = argparse.ArgumentParser(description="Orchestrator for the main pipeline.")
    parser.add_argument('--title', type=str, help='Title to be processed.')
    args = parser.parse_args()
    title = args.title if args.title else "NoCustom"
    code = ""
    
    #if no custom title in arg, we fetch from the googlesheets
    if title == "NoCustom":
        print("No custom title provided, fetching from Google Sheets...")
        title, code = get_title_from_google_sheets()
        
    if not title:
        print("❌ No title available, exiting...")
        return
        
    print(f"📝 Using title: {title}")
    print(f"📝 Using code: {code}")


    # pass the title and code to the script gen
    gen_script(title, code)

if __name__ == "__main__":
    main()