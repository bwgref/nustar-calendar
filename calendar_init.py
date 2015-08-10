import httplib2
import os
import inspect
import re

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

import time

#import datetime

import datetime
from datetime import date

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'NuSTAR Calendar'


obslist = []

# Define an observing class for below:
class obsid:
    def __init__(self, obsid, name, time_start, time_end, qa_analyst, dt): 
        self.name = name
        self.obsid = obsid
        self.time_start = time_start
        self.time_end = time_end
        self.dt = dt
        self.qa_analyst = qa_analyst

    def __str__(self):
        return "Name: %s, Time Start: %s, Time End: %s Delta Seconds: %s" % \
     (self.name, self.time_start, self.time_end, self.dt)




def read_obs_log():
    """ Reads in the observation log """

    base_epoch=datetime.datetime(2012, 6, 1)
    obsfile="observing_schedule.txt"
    with open(obsfile, 'r') as f:
        # do things with your file
        for line in f:
            fields = line.split()
            if fields[0].startswith(';'):
                continue

            thisentry = obsid(fields[2], fields[3], fields[0], fields[1], 'TBD', 0.)
            
            # Convert to UTC times
            [year, days, hr, minutes, sec] = thisentry.time_start.split(":")
            utc_date = date.fromordinal(date(int(year), 1, 1).toordinal() + int(days) - 1)
            month = utc_date.month
            day = utc_date.day
            
            utc_start_date = datetime.datetime(int(year), int(month), int(day), int(hr), int(minutes), int(sec))
            thisentry.time_start=utc_start_date.isoformat()

            [year, days, hr, minutes, sec] = thisentry.time_end.split(":")
            utc_date = date.fromordinal(date(int(year), 1, 1).toordinal() + int(days) - 1)
            month = utc_date.month
            day = utc_date.day
            utc_stop_date = datetime.datetime(int(year), int(month), int(day), int(hr), int(minutes), int(sec))

            thisentry.time_end=utc_stop_date.isoformat()
            if utc_stop_date < utc_start_date:
                print 'Munged times for: '
                print utc_start_date 
                print utc_stop_date
                print utc_stop_date - utc_start_date
                print thisentry
                print 'End munged...'
                continue

            thisentry.dt = utc_start_date - base_epoch
            
            obslist.append(thisentry)



def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('./')
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
    """ 
    This script initializes the NuSTAR Observing calendar. It nukes the
    NuSTAR calendar if it exists and then repopulates things from the AFT.
    
    It assumes that you've grabbed down the most recent AFT from the correct
    location and that it is stored in the 'observing_schedule.txt' file, which
    is the same file that drives the website.

    It takes a while to run from scratch, so you'll ant to use calendar_update.py
    for doing regular updates to the calendar.

    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)


    # Clear the old Calendar
    page_token = None
    while True:
        calendar_list = service.calendarList().list(pageToken=page_token).execute()
        for calendar_list_entry in calendar_list['items']:
            foo = calendar_list_entry['summary']
            # Get the calendar for observations
            m = re.search(r"(.Obs.)", foo)
            if m:
                print foo
                obs_calID=calendar_list_entry['id']
                print obs_calID
                service.calendars().delete(calendarId=obs_calID).execute()

        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            break



    # Make a new one:
    calendar = {
        'summary': 'NuSTAR Observations',
        'timeZone': 'UTC'
        }
    obs_calendar = service.calendars().insert(body=calendar).execute()
    obs_calID = obs_calendar['id']


    read_obs_log()

    sort_ind = sorted(range(len(obslist)), key=lambda k: obslist[k].dt)
    for ind in sort_ind:
        
#        print ind
        print obslist[ind]
        
        event = {
            "id": obslist[ind].obsid,
            "summary": obslist[ind].name,
            "start": {
                "dateTime": obslist[ind].time_start,
                "timeZone": "UTC"
                },
            "end": {
                "dateTime": obslist[ind].time_end,
                "timeZone": "UTC"
                }
            }
        event = service.events().insert(calendarId=obs_calID, body=event).execute()
        time.sleep(0.2)




if __name__ == '__main__':
    main()
