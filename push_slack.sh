#!/usr/local/bin/bash

# Check to make sure that you installed slacktee.sh
# If not, then skin this.


export PATH=${HOME}/bin:$PATH
command -v slacktee.sh > /dev/null 2>&1 || exit 1

outline=""
# See if anything failed, if yes, announce it to slack
while IFS='' read -r line || [[ -n $line ]]; do
#    if [[ $line == *FAILED* ]] ; then
#    printf '%s\n' "$line"  | $HOME/bin/slacktee.sh >> /dev/null
    outline="${outline}\n${line}"
#    outline=${printf "%s\n %s" $outline $line}
    
#    fi
#    last=$line
done < "$1"
echo -e "${outline}" | $HOME/bin/slacktee.sh >> /dev/null


