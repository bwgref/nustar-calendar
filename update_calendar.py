import httplib2
import os
import re

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

import datetime

from datetime import datetime
import pandas as pd

import time

flags = None


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """

    SCOPES = 'https://www.googleapis.com/auth/calendar'
    CLIENT_SECRET_FILE = 'client_secret.json'
    APPLICATION_NAME = 'NuSTAR Calendar'

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
    
def add_event(service, start, stop, name):
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

def add_event_quick(service, start, stop, name):

    obj = {"start" : 
                {"dateTime" : "" },
            "end" :
                {"dateTime" : "" },
            "summary" : ""
            }
            
            
    obj['start']['dateTime']=start
    obj['end']['dateTime']=stop
    obj['summary']=name

    eventadd = service.events().insert(
        calendarId='primary',
        body=obj
        ).execute()

#     eventadd = service.events().quickAdd(
#         calendarId='primary',
#         text=name
#         ).execute()
#     eventadd['start']['dateTime']=start
#     eventadd['end']['dateTime'] = stop
#     updateEvent = service.events().update(
#         calendarId='primary',eventId=eventadd['id'],
#         body=eventadd
#     ).execute()
    return
    
    
def add_new_events(service, events, aft):
    '''Main loop for adding new events
    
    Loops over the AFT and if a sequence ID is missing from the
    calendar then this calls "add_event" to add in a new calendar events
    '''
    
    for row in aft.itertuples():
        rowid = row.SequenceID
#        print(rowid)
        
        found = False
        for event in events:
            teststr=event['summary']
            if (teststr.startswith(rowid)):
                found = True
                break
            
        if not found:
            print('Adding {}'.format(rowid))
            print(row.StartTime)
            starttime = row.StartTime.to_pydatetime()
            endtime = row.EndTime.to_pydatetime()
            summary = rowid +' '+row.Target

            if ( (endtime - starttime).total_seconds() < 0):
                print("Problem!")
                print(summary)
                continue

            add_event_quick(service,
                starttime.isoformat()+'Z',
                endtime.isoformat()+'Z',
                summary)

    return 
    

def remove_all_events(service, events):
    '''Convenience function to completely erase a calendar.
    
    '''
    print('Removing all events')
    for event in events:       
        print('Removing: {}'.format(event['summary']))
        service.events().delete(
            calendarId='primary',
            eventId=event['id']).execute()
 
    return
    

def get_all_events(service):
    '''Simple wrapper to get all of the events in the calendar.
    
    Returns Google-formatted "events" object.
    
    '''
    all_events = []

    pageToken = None
    ind = 0
    while(True):
        eventsResult = service.events().list(
            calendarId='primary',timeZone='GMT',
            maxResults=2500, 
            singleEvents=True,
            orderBy='startTime',
            pageToken=pageToken).execute()
        
            
        events = eventsResult.get('items', [])
        all_events.extend(events)

        try:
            pageToken=eventsResult['nextPageToken']
        except:
            break

    return all_events


def parse_aft(infile='observing_schedule.txt', limit = 20):
    '''Parser for the AFT
    
    Reads in the observing_schedule.txt file and returns a
    Pandas dataframe.
    
    '''
    now = datetime.utcnow()
    
    seqid = []
    seqname = []
    start_time = []
    end_time = []

    f = open(infile, 'r')
    for line in f:
        if line.startswith(";"):
            continue
        fields = line.split()

        dtm = fields[0].split(':')
        start_time.extend([datetime.strptime(dtm[0]+' ' +dtm[1]+' '+dtm[2]+' '+ \
            dtm[3]+' '+dtm[4], '%Y %j %H %M %S')])

        dtm = fields[1].split(':')
        end_time.extend([datetime.strptime(dtm[0]+' ' +dtm[1]+' '+dtm[2]+' '+ \
            dtm[3]+' '+dtm[4], '%Y %j %H %M %S')])

        seqid.extend([fields[2]])
        seqname.extend([fields[3]])

    d = {'StartTime' : start_time, 
      'EndTime'  : end_time, 
      'SequenceID' : seqid,
      'Target' : seqname}
    df = pd.DataFrame(d)
    
    df.sort_values('StartTime', inplace=True)
    return df
    f.close
    
    
def clean_stale_events(service, events, aft):
    '''Remove any events from the calendar that no longer appear in the AFT.
    
    Since we project into the future, this deals with any chances to the schedule.
    
    '''
    
    for event in events:
        obsid = (event['summary'].split())[0]
        # Check to see if this exists in the AFT:
        match = aft.loc[aft['SequenceID'] == obsid]
        if len(match) == 0 :
            print('Removing: ',start, event['summary'])

            service.events().delete(
                calendarId='primary',
                eventId=event['id']).execute()
    return


def remove_duplicates(service, events, aft):
    '''Remove any duplicate events

    '''
    
    for row in aft.itertuples():
        rowid = row.SequenceID
        # Check to see if you're already in the events
#        print(rowid)
         
        # Query the calendar to see if how many entries match this one
        eventsResult = service.events().list(calendarId='primary', q=rowid).execute()

        found_events = eventsResult.get('items', [])

        for ind2, found_event in enumerate(found_events):
            if ind2 == 0:
                continue
            else:
                print('Removing one:')
                print(found_event)
                service.events().delete(
                    calendarId='primary',
                    eventId=found_event['id']).execute()
    return

def init_service():
    '''Wrapper script to set up the Google credentials.
    
    Calls get_credentials() which does the actual work.
    
    Returns a Google 'server' object.
    
    '''
    
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    return service
    



def main():
    ''' Main functional loop'
    
    '''


    print("Updating calendar.")
    
    # Set things up
    service = init_service()
    aft = parse_aft()
    events = get_all_events(service)

    # Clean out events that don't exist any more
    clean_stale_events(service, events, aft)

    # Add in new events
    add_new_events(service, events, aft)

    return

if __name__ == "__main__":
    main()

