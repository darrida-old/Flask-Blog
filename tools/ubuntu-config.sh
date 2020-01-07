#!/bin/bash
#
#Purpose of script:
#  -Expidite setting heroku config each time
#
##############################################
export FLASK_APP=flasky.py
export FLASK_CONFIG=development
export FLASKY_ADMIN=bentestflask@gmail.com
export SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
export MAIL_USERNAME=bentestflask@gmail.com
echo ""
echo "Ubuntu configuration complete."
echo "***Manually set MAIL_PASSWORD*** - using 'set MAIL_PASSWORD=[password]'"
echo ""
##############################################
# Contact: darrida | darrida.py@gmail.com | tech.theogeek.com
