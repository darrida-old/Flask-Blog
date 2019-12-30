#!/bin/bash
#
#Purpose of script:
#  -Expidite setting heroku config each time
#
##############################################
sudo heroku config:set FLASK_APP=flasky.py
sudo heroku config:set FLASK_CONFIG=development
sudo heroku config:set FLASKY_ADMIN=bentestflask@gmail.com
sudo heroku config:set SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
sudo heroku config:set MAIL_USERNAME=bentestflask@gmail.com
echo ""
echo "Ubuntu configuration complete."
echo "***Manually set MAIL_PASSWORD*** - using 'set MAIL_PASSWORD=[password]'"
echo ""
##############################################
# Contact: darrida | darrida.py@gmail.com | tech.theogeek.com
