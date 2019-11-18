#!/usr/bin/env bash

#in crontab
## m h  dom mon dow   command
#00 01 * * * find /home/test/screen_shots/. -mtime +180 -exec rm -rf {} \;
#30 01 * * * find /home/test/slave_logs/. -mtime +180 -exec rm -rf {} \;
#00 02 1 * * /home/active/prejudge_service/venv/bin/python /home/active/prejudge_service/available.py > /home/active/prejudge_service/start.log
#@reboot /home/active/reboot_services/file_service.sh

NGINX_ROOT="/usr"
if ps ax | grep -v grep | grep nginx > /dev/null
then
  echo "nginx running"
else
  $NGINX_ROOT/sbin/nginx
fi

if ps ax | grep -v grep | grep uwsgi > /dev/null
then
  echo "uwsgi running"
else
  source /home/active/prejudge_service/venv/bin/activate
  uwsgi /home/active/prejudge_service/configuration/uwsgi.ini
fi