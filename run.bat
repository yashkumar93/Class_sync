@echo off
echo Starting Class Sync...
echo (Since this is a Django project, both the frontend templates and the backend run together)
echo.

if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Proceeding with global Python...
)

echo.
echo Starting development server...
python manage.py runserver

pause
