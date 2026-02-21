@echo off
echo Сборка HomRec.exe...
pip install pyinstaller opencv-python
pyinstaller --onefile --windowed --icon=../icons/homrec.ico --name=HomRec ../HomRec.py
echo Готово!
pause