@echo off
REM מפעיל את גרסת הקוד העדכנית (עם כפתורי LIN ו-BBO), לא את ה-exe הישן.
cd /d "%~dp0"
start "" "C:\Users\PC\AppData\Local\Programs\Python\Python312\pythonw.exe" "bridge_teacher.py"
