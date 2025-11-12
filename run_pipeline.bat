@echo off
title Greyhound DOCX → Excel/CSV Extractor
echo ================================================
echo   GREYHOUND RACING DOCX → EXCEL/CSV PIPELINE
echo ================================================
echo.

REM --- 1️⃣ Set up environment ---
if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
)
call venv\Scripts\activate

REM --- 2️⃣ Install requirements if needed ---
if not exist venv\Lib\site-packages\docx (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM --- 3️⃣ Run main pipeline ---
echo.
echo Running DOCX extraction pipeline...
python main.py
echo.

REM --- 4️⃣ Display output location ---
echo ✅ Pipeline complete!
echo Outputs saved to:
echo   outputs\all_dogs_master.xlsx
echo   outputs\all_dogs_master.csv
echo Logs:
echo   outputs\logs\
echo.
pause
