# GmailRead.py
from __future__ import print_function
import base64
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_text_body(message):
    try:
        if 'parts' in message['payload']:
            parts = message['payload']['parts']
            for part in parts:
                if part['mimeType'] == 'text/plain':
                    text = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    return text
        else:
            if message['payload']['mimeType'] == 'text/plain':
                text = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
                return text
        return ''
    except KeyError as error:
        print(f'An error occurred: {error}')
        return ''


def get_unread_messages_last_message(credentials):
    try:
        service = build('gmail', 'v1', credentials=credentials)

        unread_msgs = service.users().messages().list(
            userId='me', q='is:unread', maxResults=None).execute()

        messages = unread_msgs.get('messages', [])

        unread_data = []

        for message in messages:
            msg = service.users().messages().get(
                userId='me', id=message['id']).execute()
            thread_id = msg['threadId']
            thread = service.users().threads().get(userId='me', id=thread_id).execute()
            thread_messages = thread['messages']
            last_message = thread_messages[-1]

            text_body = get_text_body(last_message)

            # Check for duplicate message_id
            if not any(item["message_id"] == last_message["id"] for item in unread_data):
                # Clean up text_body by splitting lines, removing quoted text and metadata, and rejoining
                lines = text_body.split("\n")
                clean_lines = [line.strip() for line in lines if not line.startswith(">") and not line.startswith("On ") and not line.startswith("--") and not line.lower().startswith("sent from my iphone") and not (":" in line and "http" not in line)]
                clean_text_body = " ".join(clean_lines).strip()
                clean_text_body = clean_text_body.replace("\\", "")

                headers = last_message["payload"]["headers"]
                date = next((header["value"] for header in headers if header["name"] == "Date"), "")
                lead = next((header["value"] for header in headers if header["name"] == "From"), "")
                email_match = re.search(r'<(.+?)>', lead)
                email = email_match.group(1) if email_match else ""
                lead = re.sub(r'\\|"', '', lead)
                lead = re.sub(r'<(.+?)>', '', lead).strip()
                lead = re.sub(r'\+', '', lead)

                unread_data.append({"message_id": last_message["id"], "text_body": clean_text_body, "date": date, "lead": lead, "email": email})

        return unread_data

    except HttpError as error:
        print(F'An error occurred: {error}')
        return []