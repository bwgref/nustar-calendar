import httplib2
import os

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

import datetime

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'NuSTAR Calendar'

def read_obs_log();
    """ Reads in the observation log """
    obsfile="observing_schedule.txt"
    

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatability with Python 2.6
            credentials = tools.run(flow, store)
        print 'Storing credentials to ' + credential_path
    return credentials

def main():
    """Shows basic usage of the Google Calendar API.

    Creates a Google Calendar API service object and outputs a list of the next
    10 events on the user's calendar.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time


# Calendar ID is NuSTAR Observations
    obs_cal_id='oaej5g959eckmgjctggjicdq7g@group.calendar.google.com'
    created_event = service.events().quickAdd(
                                              calendarId=obs_cal_id,
                                              text='Appointment at Somewhere on June 3rd 10am-10:25am').execute()

    ev_id = created_event['id']

    page_token = None
    while True:
        events = service.events().list(calendarId=obs_cal_id, pageToken=page_token).execute()
        for event in events['items']:
            print event['summary']
            print event['id']
        page_token = events.get('nextPageToken')
        if not page_token:
            break

#    page_token = None
#    while True:
#      calendar_list = service.calendarList().list(pageToken=page_token).execute()
#      for calendar_list_entry in calendar_list['items']:
#        print calendar_list_entry['summary']
#        print calendar_list_entry['id']
#      page_token = calendar_list.get('nextPageToken')
#      if not page_token:
#        break

#    print 'Getting the upcoming 10 events'
#    eventsResult = service.events().list(
#        calendarId='primary', timeMin=now, maxResults=10, singleEvents=True,
#        orderBy='startTime').execute()
#
#    events = eventsResult.get('items', [])
#
#    if not events:
#        print 'No upcoming events found.'
#    for event in events:
#        start = event['start'].get('dateTime', event['start'].get('date'))
#        print start, event['summary']


if __name__ == '__main__':
    main()
