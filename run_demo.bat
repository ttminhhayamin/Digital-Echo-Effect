@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === Digital Echo Effect - DGT302 ===
echo Dang kiem tra thu vien (lan dau co the mat 1-2 phut)...
python -m pip install -r requirements.txt --quiet --disable-pip-version-check
echo Dang khoi dong... Trinh duyet se tu mo tai http://localhost:8501
echo (Dong cua so nay de tat demo)
start "" cmd /c "timeout /t 4 >nul & start http://localhost:8501"
python -m streamlit run app.py
pause