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
    
    
def add_new_events(service, events, aft):
    '''Main loop for adding new events
    
    Loops over the AFT and if a sequence ID is missing from the
    calendar then this calls "add_event" to add in a new calendar events
    '''
    
    for row in aft.itertuples():
        rowid = row.SequenceID
        # Check to see if you're already in the events
        match = False

        for event in events:
            obsid = (event['summary'].split())[0]
            if obsid == rowid:
                match = True
        if match:
            continue
        else:
            print('Adding {}'.format(rowid))
            starttime = row.StartTime.to_pydatetime()
            endtime = row.EndTime.to_pydatetime()
            summary = rowid +' '+row.Target
            add_event(service, starttime.isoformat()+'Z', endtime.isoformat()+'Z', summary)
                
# Defunct
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

        date = dtm_spl[0].split('-')
        time_fields = dtm_spl[1].split('-')
        time = time_fields[0].split(':')
        start_time = datetime.datetime.strptime(date[0]+' ' +date[1]+' '+date[2]+' '+ \
            time[0]+' '+time[1]+' '+time[2][:2], '%Y %m %d %H %M %S')
        if (now - start_time).days > abs(limitdays):
            continue

        print('Removing: ',start, event['summary'])

        service.events().delete(
            calendarId='primary',
            eventId=event['id']).execute()
 


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
    eventsResult = service.events().list(
    calendarId='primary',timeZone='GMT', singleEvents=True,
    maxResults=200000,
    orderBy='startTime').execute()
    events = eventsResult.get('items', [])
    return events


 
# Defunct
def populate_calendar(limit):

    now = datetime.datetime.utcnow()
    
    f = open('observing_schedule.txt', 'r')
    for line in f:
        if line.startswith(";"):
            continue
        fields = line.split()

        dtm = fields[0].split(':')
        start_time = datetime.datetime.strptime(dtm[0]+' ' +dtm[1]+' '+dtm[2]+' '+ \
            dtm[3]+' '+dtm[4], '%Y %j %H %M %S')

        dtm = fields[1].split(':')
        end_time = datetime.datetime.strptime(dtm[0]+' ' +dtm[1]+' '+dtm[2]+' '+ \
            dtm[3]+' '+dtm[4], '%Y %j %H %M %S')

        if (now - start_time).days > abs(limit):
            break
        seqid = fields[2]
        seqname=fields[3]

        coords = line.find('[')
        qa_start = line.find('[', coords+1)
        qa_person=''
        if(qa_start != -1):
            qa_end =  line.find(']', qa_start)
            qa_person = line[qa_start+1:qa_end]

        print('Adding: ', start_time.isoformat()+'Z', end_time.isoformat()+'Z', seqid+' '+seqname+' ('+qa_person+')')
        add_event(start_time.isoformat()+'Z', end_time.isoformat()+'Z', seqid+' '+seqname+' ('+qa_person+')')


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

