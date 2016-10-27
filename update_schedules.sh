#!/bin/bash
for stub in qa observing
do
    cp -p ${stub}_schedule.txt ${stub}_old_schedule.txt
done
curl -Rs --netrc-file nusoc_password.txt -O "http://www.srl.caltech.edu/NuSTAR_Public/NuSTAROperationSite/Operations/{qa,observing}_schedule.txt"

python update_calendar.py
