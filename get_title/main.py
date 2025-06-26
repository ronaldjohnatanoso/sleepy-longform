# This script takes an available title from the googlesheets or also just supply with your custom

import os
import re
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
import time

load_dotenv()  # Load environment variables from .env file one level up

# 👇 Get Google Sheet URL from environment variable
sheet_url = os.getenv('GOOGLE_SHEET_URL')
sheet_tab = 'TITLES'
credentials_json_path = './credentials.json'

# Initialize service once globally
def get_sheets_service():
    """Get authenticated Google Sheets service"""
    credentials = Credentials.from_service_account_file(
        credentials_json_path,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    return build('sheets', 'v4', credentials=credentials)

def extract_sheet_id(url):
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    return match.group(1) if match else None

def get_title_from_google_sheets():
    """Fetch the first available title from Google Sheets with simple retry"""
    max_retries = 20
    
    for attempt in range(max_retries):
        if attempt > 0:
            print(f'🔄 Retry attempt {attempt}...')
            time.sleep(0.5)  # Brief pause before retry
        
        title = try_get_title()
        if title:
            return title
    
    print('❌ Failed to get title after retries')
    return None

def try_get_title():
    """Single attempt to get and claim a title"""
    if not sheet_url:
        print('❌ GOOGLE_SHEET_URL environment variable is not set.')
        return None
        
    spreadsheet_id = extract_sheet_id(sheet_url)
    if not spreadsheet_id:
        print('❌ Could not extract spreadsheet ID from URL.')
        return None
    
    service = get_sheets_service()  # Use global service function
    
    # Read all data from the TITLES sheet
    range_name = f'{sheet_tab}!A:D'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()
    
    values = result.get('values', [])
    if not values:
        print('❌ No data found in the sheet.')
        return None
    
    # Find first available title
    for i, row in enumerate(values[1:], start=2):
        if len(row) == 0:
            continue
            
        title = row[0] if len(row) > 0 else ""
        is_taken = row[1] if len(row) > 1 else ""
        
        if title and not is_taken:
            title_info = {
                'title': title,
                'row_number': i,
                'spreadsheet_id': spreadsheet_id
            }
            
            # Try to claim it (pass service)
            if mark_title_as_taken_safe(service, title_info):
                return title
            else:
                # Someone else got it, retry whole process
                return None
    
    print('❌ No available titles found.')
    return None

def mark_title_as_taken_safe(service, title_info):
    """Safely mark title as taken with verification"""
    try:
        # Double-check it's still available
        check_range = f'{sheet_tab}!B{title_info["row_number"]}'
        current_result = service.spreadsheets().values().get(
            spreadsheetId=title_info['spreadsheet_id'],
            range=check_range
        ).execute()
        
        current_values = current_result.get('values', [['']])
        current_is_taken = current_values[0][0] if current_values and current_values[0] else ""
        
        if current_is_taken:  # Someone else took it
            return False
        
        # Still available, mark it
        body = {'values': [['YES']]}
        service.spreadsheets().values().update(
            spreadsheetId=title_info['spreadsheet_id'],
            range=check_range,
            valueInputOption='RAW',
            body=body
        ).execute()
        
        print(f'✅ Successfully claimed: "{title_info["title"]}"')
        return True
        
    except Exception as e:
        print(f'❌ Error claiming title: {e}')
        return False

# use this for testing purposes, pipeline calls the exact function
if __name__ == '__main__':
    try:
        # Get the first available title
        title = get_title_from_google_sheets()
        
        if title:
            print(f'\n📝 Selected title: {title}')
        else:
            print('No available titles found.')
            
    except Exception as e:
        print(f'❌ Error: {e}')