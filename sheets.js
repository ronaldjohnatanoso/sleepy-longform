const { google } = require('googleapis');
const fs = require('fs');

// 👇 Paste your full Google Sheet URL here
const sheetUrl = 'https://docs.google.com/spreadsheets/d/1-qbJ5QCw_hpCeTDgRkp--G3FVBXcujMQVWHXtfBuoW4/edit?gid=0#gid=0';

// 👇 Name of the sheet tab (NOT the spreadsheet title!)
const sheetTab = 'Sheet1'; // Check the tab name at the bottom of your sheet

// 👇 Function to extract spreadsheet ID from URL
function extractSheetId(url) {
  const match = url.match(/\/d\/([a-zA-Z0-9-_]+)/);
  return match ? match[1] : null;
}

async function appendToSheet() {
  const spreadsheetId = extractSheetId(sheetUrl);

  if (!spreadsheetId) {
    console.error('❌ Could not extract spreadsheet ID from URL.');
    return;
  }

  const auth = new google.auth.GoogleAuth({
    keyFile: './credentials.json', // Path to service account JSON
    scopes: ['https://www.googleapis.com/auth/spreadsheets'],
  });

  const client = await auth.getClient();
  const sheets = google.sheets({ version: 'v4', auth: client });

  const range = `${sheetTab}!A1`;

  const result = await sheets.spreadsheets.values.append({
    spreadsheetId,
    range,
    valueInputOption: 'RAW',
    insertDataOption: 'INSERT_ROWS',
    requestBody: {
      values: [
        [new Date().toISOString(), 'some-data', 'more-datssa'],
      ],
    },
  });

  console.log('✅ Row appended:', result.statusText);
}

appendToSheet().catch(console.error);
