#!/usr/bin/env bash
/home/$APP_USR/.local/bin/gunicorn djangobackend.wsgi:application --daemon -c /home/$APP_USR/.gcorn.conf
sudo nginx -t && sudo nginx -g "daemon off;"

