import datetime
import os.path
import pytz
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_calendar_events(credentials):

    try:
        service = build('calendar', 'v3', credentials=credentials)

        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=10, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            return []

        event_list = []
        for event in events:
            # print(event)
            start = event['start'].get('dateTime', event['start'].get('date'))
            start_time = datetime.datetime.fromisoformat(start).replace(tzinfo=datetime.timezone.utc)
            est_tz = pytz.timezone("US/Eastern")
            est_time = start_time.astimezone(est_tz)
            est_time += datetime.timedelta(hours=4)
            est_time = est_time.strftime("%Y-%m-%d %I:%M %p")
            event_data = {
                "name": event.get("summary", ""),
                "day": est_time.split(" ")[0],
                "time": est_time.split(" ")[1] + " " + est_time.split(" ")[2],
                "status": event.get("status", ""),
                "guest_names": ", ".join([attendee.get("displayName", "") for attendee in event.get("attendees", [])]),
                "guest_emails": ", ".join([attendee.get("email", "") for attendee in event.get("attendees", [])]),
                "google_meet_link": event.get("hangoutLink", ""),
            }
            event_list.append(event_data)

        return event_list

    except HttpError as error:
        print('An error occurred: %s' % error)
        return []

