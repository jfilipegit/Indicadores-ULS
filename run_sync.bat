@echo off
cd /d "c:\Users\jfili\Documents\Indicadores SNS"
python "c:\Users\jfili\Documents\Indicadores SNS\update_from_api.py" >> sync_log.txt 2>&1
