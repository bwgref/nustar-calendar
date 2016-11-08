#!/bin/bash

export PATH=/disk/lif2/bwgref/miniconda3/bin:$PATH

SRCDIR=/disk/lif2/bwgref/git/nustar-calendar/
HERE=`pwd`


cd $SRCDIR



cp -p observing_schedule.txt observing_old_schedule.txt


if [[ $HOSTNAME == "lif" ]] ; then

    cp -p /home/nustar1/Web/NuSTAROperationSite/Operations/observing_schedule.txt .

else 
    curl -Rs --netrc-file nusoc_password.txt -O "http://www.srl.caltech.edu/NuSTAR_Public/NuSTAROperationSite/Operations/observing_schedule.txt"
fi


#if test observing_schedule.txt -nt observing_old_schedule.txt; then
#    echo "New schedule found." > cal.log
python update_calendar.py #>> cal.log    
#    ./push_slack.sh cal.log >> /dev/null
#fi
#else
#    echo "No new schedule found." > cal.log
#    ./push_slack.sh cal.log >> /dev/null
#fi


cd $HERE    