# HydroTrack — Water Reminder App

A beginner-friendly Flask app for setting a daily water goal, tracking water intake, and getting browser reminders.

## Features

- Calculates a daily water goal from weight using the original `0.033 L/kg` formula.
- Converts the goal into 250 ml glasses.
- Tracks water intake and daily progress.
- Lets you pause reminders and record a missed reminder.
- Plays a selected browser beep and can show browser notifications while the page is open.
- Uses a responsive, single-page dashboard.

## Requirements

- Python 3
- Flask (installed from `requirements.txt`)

## Run locally

Open PowerShell in this project folder and run:

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000> in your browser. Keep the PowerShell window and browser page open while using reminders.

## Project files

```text
app.py                 Flask app and API routes
menu.py                Water goal and glass tracking logic
requirements.txt       Python dependencies
templates/index.html   Dashboard page
static/style.css       Page styling
static/script.js       Browser interactions and Flask requests
```

## How it works

The page sends requests to Flask using JavaScript `fetch()`. Flask returns dashboard data as JSON, and the page updates without reloading. The water goal and glass calculations are in `menu.py`.

## Notes

- Browser reminders work only while the app page is open. Allow notifications in your browser to see them.
- App data is kept in memory and resets when the Flask server stops or restarts.
- Water amounts must be entered in 250 ml increments, matching the app's glass-based tracking.
- `python app.py` runs Flask's development server and is intended for local development. Hosting publicly requires a production hosting service.
