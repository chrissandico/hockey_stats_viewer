# Setting Up Google Sheets Credentials for Local Testing

## Overview
To test the hockey stats webapp locally, you need to set up Google Sheets API credentials. This guide will walk you through the process.

## Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your project ID (you'll need this later)

## Step 2: Enable Google Sheets API

1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google Sheets API"
3. Click on it and press "Enable"
4. Also enable "Google Drive API" (needed for accessing sheets)

## Step 3: Create Service Account Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Fill in the service account details:
   - Name: `hockey-stats-service`
   - Description: `Service account for hockey stats webapp`
4. Click "Create and Continue"
5. Skip the optional steps and click "Done"

## Step 4: Generate and Download Key

1. In the "Credentials" page, find your service account
2. Click on the service account email
3. Go to the "Keys" tab
4. Click "Add Key" > "Create New Key"
5. Choose "JSON" format
6. Click "Create" - this will download a JSON file

## Step 5: Set Up Local Credentials

### Option A: Using credentials.json file (Recommended for local development)

1. Rename the downloaded JSON file to `credentials.json`
2. Copy it to your project root directory (same level as this README)
3. **IMPORTANT**: Make sure `credentials.json` is in your `.gitignore` file to avoid committing secrets

### Option B: Using Environment Variable (Production-like setup)

1. Set the `GOOGLE_CREDENTIALS` environment variable with the JSON content:

**Windows (PowerShell):**
```powershell
$env:GOOGLE_CREDENTIALS = Get-Content -Path "path\to\your\downloaded\file.json" -Raw
```

**Windows (Command Prompt):**
```cmd
set GOOGLE_CREDENTIALS={"type":"service_account",...}
```

**Linux/Mac:**
```bash
export GOOGLE_CREDENTIALS='{"type":"service_account",...}'
```

## Step 6: Share Google Sheet with Service Account

1. Open your Google Sheet (HockeyStatsDB)
2. Click "Share" in the top right
3. Add the service account email (found in your credentials JSON file)
4. Give it "Editor" permissions
5. Click "Send"

## Step 7: Configure Sheet ID (if different)

If you're using a different Google Sheet, update the sheet ID in the code:

1. Get your sheet ID from the URL: `https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit`
2. Update `hockey_stats_webapp/services/sheets_service.py` if needed

## Step 8: Test the Connection

Run the test script to verify everything is working:

```bash
python test_google_sheets_connection.py
```

## Step 9: Analyze Sheet Structure (Optional)

To get detailed information about your Google Sheet structure and identify the exact column names:

```bash
python analyze_sheet_structure.py
```

This will:
- Show all column names in each sheet
- Identify the correct ID column name for players
- Generate specific fix recommendations if needed
- Save detailed analysis to `sheet_structure_analysis.json`

## Troubleshooting

### Common Issues:

1. **"Credentials not found"**: Make sure `credentials.json` is in the right location
2. **"Permission denied"**: Ensure the service account email is shared with the Google Sheet
3. **"API not enabled"**: Make sure both Google Sheets API and Google Drive API are enabled
4. **"Invalid credentials"**: Check that the JSON file is valid and complete

### Security Notes:

- Never commit `credentials.json` to version control
- Use environment variables for production deployments
- Regularly rotate service account keys for security
- Only grant minimum necessary permissions

## File Structure

Your project should look like this:
```
hockey_stats_webapp_2/
├── credentials.json          # Your service account key (local only)
├── credentials.json.sample   # Template file
├── hockey_stats_webapp/
│   ├── app.py
│   └── services/
│       └── sheets_service.py
└── test_google_sheets_connection.py
```

## Next Steps

Once credentials are set up:
1. Run `python test_google_sheets_connection.py` to test the connection
2. Run `python debug_column_structure.py` to see the actual data structure
3. Start the webapp with `python hockey_stats_webapp/app.py`

The webapp should now connect to Google Sheets successfully and you can test the full functionality locally.
