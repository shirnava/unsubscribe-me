from __future__ import print_function
import pickle
import os.path
import base64
import re
import webbrowser
from bs4 import BeautifulSoup

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Read-only Gmail access
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def main():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    nextPageToken = None
    ignore = {}

    # Keep running until we've processed all pages
    while True:
        # Call the Gmail API
        results = service.users().messages().list(userId='me', pageToken=nextPageToken).execute()

        # Last page has no messages
        if 'messages' not in results:
            print('Completed')
            break;
        else:
            # Load email contents
            print('Loading e-mails')

            messages = results["messages"]
            nextPageToken = results["nextPageToken"]
            
            for message in messages:
                # Get email content by email ID
                email = service.users().messages().get(userId='me', id=message["id"]).execute()

                # Check for email body
                if 'data' in email['payload']['body']:
                    base64data = email['payload']['body']['data']

                    # Decode base64 urlencoded email body
                    body = base64.urlsafe_b64decode(base64data).decode('utf-8')

                    # Check for unsubscribe wording in link text
                    if "unsubscribe" in body.lower():
                        # Get email headers to extract sender name
                        headers = email['payload']['headers']
                        for header in headers:
                            # Find 'From' header
                            if header['name'] == 'From':
                                sender = header['value']
                                # Check if we already asked the user about this sender
                                if sender not in ignore:
                                    # Parse HTML string with BeautifulSoup to extract <a> links
                                    soup = BeautifulSoup(body, features="html.parser")

                                    # Check all <a> links for unsubscribe text
                                    for tag in soup.findAll('a', href=True):
                                        if "unsubscribe" in str(tag.string).lower():
                                            link = tag['href']

                                            # Ask the user if they want to unsubscribe from this sender
                                            cont = input("Do you want to unsubscribe from    " + sender + '   (y/n): ')

                                            # Don't ask about this sender again
                                            ignore[sender] = True

                                            if cont == "y":
                                                # Open unsubscribe link in default browser (Chrome?)
                                                webbrowser.get('windows-default').open(link,new=2)
                                                    

                                    
                    
                    
            

if __name__ == '__main__':
    main()
