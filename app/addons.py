# Based on quickstart.py from Google API documentation

from __future__ import print_function
import pickle
import os.path
from datetime import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

#### ISAW Customization ####
# The ID and range of the BSN Add-on sheet
SPREADSHEET_ID = '12ewTErqG3h2ToDdn97WQmdW59_xiowfr2T3I3GaTsk8'
RANGE_NAME = 'BSN_Columns'
############################

def get_addons(sample_date):
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('../token.pickle'):
        with open('../token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('../token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=RANGE_NAME).execute()
    values = result.get('values', [])
    bsn_addons = []

    if not values:
        print('No data found.')
    else:
        for row in values[1:]:
            bsn_addons.append(row)

    bsn_addons_current = []

    for bsn_addon in bsn_addons:
        bsn_date = datetime.strptime(bsn_addon[0], '%m/%d/%Y')
        if  bsn_date.strftime('%Y') == sample_date.strftime('%Y') and bsn_date.strftime('%m') == sample_date.strftime('%m'):
            bsn_addons_current.append(bsn_addon[1])
    # print(f'Returned the following addons:\n{bsn_addons_current}')
    return bsn_addons_current

if __name__ == '__main__':
    get_bsn_addons()
