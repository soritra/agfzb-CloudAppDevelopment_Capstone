#!/usr/bin/env bash
#cd /home/${APP_USR}/app/?
# Make migrations and migrate the database.
echo "Making migrations and migrating the database. "
python manage.py makemigrations --nopinut
python manage.py migrate --nopinut 
exec "$@"

