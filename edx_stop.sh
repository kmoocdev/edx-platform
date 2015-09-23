service nginx stop
service supervisor stop
service supervisor.devpi stop
pkill -u www-data
rm -rf /edx/var/edxapp/staticfiles/*
sudo -H -u edxapp bash -c "./compile.sh"
./edx_start.sh
