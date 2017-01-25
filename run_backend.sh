if [ "$log_level" = "" ]
then
   echo "Running backend with loglevel warning"
   loglevel=warning
else
   echo "Running backend with loglevel $log_level"
fi
python runserver.py
celery worker -A flauthority.celery --loglevel=$log_level

