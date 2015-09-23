source /edx/app/edxapp/edxapp_env
cd /edx/app/edxapp/edx-platform
paver update_assets cms --settings=aws
paver update_assets lms --settings=aws
