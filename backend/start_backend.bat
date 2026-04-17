@echo off
cd /d "C:\Users\PRON_KBJ\Desktop\weekly boss dashboard\backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8002
pause
