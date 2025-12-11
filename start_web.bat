@echo off
echo ===================================
echo Starting AI Council Web Interface
echo ===================================
echo.
echo Installing/updating dependencies...
pip install -r requirements.txt
echo.
echo Starting web server...
echo Open your browser to: http://localhost:5000
echo.
python web_council.py

