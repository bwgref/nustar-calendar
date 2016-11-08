import httplib2
import os
import re

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

import datetime

# try:
#     import argparse
#     flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
# except ImportError:
flags = None

SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'NuSTAR Calendar'

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

        credentials = tools.run_flow(flow, store, flags)
#        else: # Needed only for compatability with Python 2.6
#            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials
    
def add_event(start, stop, name):
    eventadd = service.events().quickAdd(
        calendarId='primary',
        text=name
        ).execute()
    eventadd['start']['dateTime']=start
    eventadd['end']['dateTime'] = stop
    updateEvent = service.events().update(
        calendarId='primary',eventId=eventadd['id'],
        body=eventadd
    ).execute()
    return
    
def cleanup_calendar(limitdays):

    now = datetime.datetime.utcnow()
    limit = (now + datetime.timedelta(-limitdays))
    limstr = limit.isoformat()+'Z'
    
    
    print('Removing the previous '+str(limitdays)+' days')
    eventsResult = service.events().list(
        calendarId='primary',timeZone='GMT', timeMin=limstr, singleEvents=True,
        maxResults=2000,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        dtm = start
        dtm_spl = dtm.split('T')
#        print(dtm_spl)

        date = dtm_spl[0].split('-')
        time_fields = dtm_spl[1].split('-')
        time = time_fields[0].split(':')
        start_time = datetime.datetime.strptime(date[0]+' ' +date[1]+' '+date[2]+' '+time[0]+' '+time[1]+' '+time[2][:2], '%Y %m %d %H %M %S')
        if (now - start_time).days > abs(limitdays):
            continue


        print('Removing: ',start, event['summary'])

        service.events().delete(
            calendarId='primary',
            eventId=event['id']).execute()
            
def populate_calendar(limit):

    now = datetime.datetime.utcnow()

    f = open('observing_schedule.txt', 'r')
    for line in f:
        if line.startswith(";"):
            continue
        fields = line.split()

        dtm = fields[0].split(':')
        start_time = datetime.datetime.strptime(dtm[0]+' ' +dtm[1]+' '+dtm[2]+' '+dtm[3]+' '+dtm[4], '%Y %j %H %M %S')

        dtm = fields[1].split(':')
        end_time = datetime.datetime.strptime(dtm[0]+' ' +dtm[1]+' '+dtm[2]+' '+dtm[3]+' '+dtm[4], '%Y %j %H %M %S')

        if (now - start_time).days > abs(limit):
            break
        seqid = fields[2]
        seqname=fields[3]

        print('Adding: ', start_time.isoformat()+'Z', end_time.isoformat()+'Z', seqid+' '+seqname)
        add_event(start_time.isoformat()+'Z', end_time.isoformat()+'Z', seqid+' '+seqname)



import os

old_filename = "observing_old_schedule.txt"
new_filename= "observing_schedule.txt"


print("Updating calendar.")
credentials = get_credentials()
http = credentials.authorize(httplib2.Http())
service = discovery.build('calendar', 'v3', http=http)
cleanup_calendar(14)
populate_calendar(14)

