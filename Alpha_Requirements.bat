@echo off
title Alpha AI - Setup

echo ==========================================
echo        ALPHA AI - AUTOMATIC SETUP
echo ==========================================
echo.

echo Checking Python installation...
python --version >nul 2>&1

if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python first.
    echo.
    pause
    exit /b 1
)

echo Python found.
echo.

echo Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Installing required modules...
echo.

python -m pip install pyttsx3 requests pyautogui pywhatkit python-dotenv

if errorlevel 1 (
    echo.
    echo ==========================================
    echo       MODULE INSTALLATION FAILED
    echo ==========================================
    echo.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo       ALL MODULES INSTALLED
echo ==========================================
echo.

echo Starting Alpha AI...
echo.

python alpha.py

echo.
echo Alpha has stopped.
pause
