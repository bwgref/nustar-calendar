import httplib2
import os

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

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


obs_time_start = {}
obs_time_end = {}
obs_name = {}

def read_obs_log( obs_time_start, obs_time_end, obs_name ):
    #global obs_time_start obs_time_end # obs_name
    """ Reads in the observation log """
    obsfile="observing_schedule.txt"
    with open(obsfile, 'r') as f:
        # do things with your file
        for line in f:
            fields = line.split()
            if fields[0].startswith(';'):
                continue
            obsid=fields[2]
            obs_time_start[obsid]=fields[0]
            obs_time_end[obsid]=fields[1]
            obs_name[obsid]=fields[3]


def main():
    #    global obs_time_start obs_time_end
    read_obs_log(obs_time_start,obs_time_end,obs_name)

    base_epoch=datetime.datetime(2011, 1, 1)

    for obsid in obs_time_start:
# Convert the time to normal units:
        [year, days, hr, minutes, sec] = obs_time_start[obsid].split(":")
        utc_date = date.fromordinal(date(int(year), 1, 1).toordinal() + int(days) - 1)
        month = utc_date.month
        day = utc_date.day

        utc_date = datetime.datetime(int(year), int(month), int(day), int(hr), int(minutes), int(sec))

        this_dt = utc_date - base_epoch
        dt[obsid]= this_dt.days * 865400. + this_dt.seconds
        utc_start = utc_date.strftime('%Y-%m-%dT%H:%M:%S')


     sort_inds = sorted(range(len(s)), key=lambda k: s[k])






#        dt = utc_date - base_epoch
#        print dt.
#        break

#        [year, days, hr, min, sec] = obs_time_end[obsid].split(":")
#        utc_date = date.fromordinal(date(int(year), 1, 1).toordinal() + int(days) - 1)
#        utc_end = utc_date.strftime('%Y-%m-%d') + "T"+ hr + ':' + min + ':'+sec
#
#        event = {
#            "id": obsid,
#            "summary": obs_name[obsid],
#            "start": {
#                "dateTime": utc_start,
#                "timeZone": "UTC"
#            },
#            "end": {
#                "dateTime": utc_end,
#                "timeZone": "UTC"
#            }
#        }


if __name__ == '__main__':
    main()
