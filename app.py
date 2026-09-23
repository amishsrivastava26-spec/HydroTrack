from datetime import datetime

from flask import Flask, jsonify, render_template, request

from menu import daily_goal, record_drink, recommended_glasses

app = Flask(__name__)


water_data = {
    "name": "",
    "age": None,
    "weight": None,
    "goal_liters": 0,
    "goal_glasses": 0,
    "water_count": 0,
    "missed_count": 0,
    "interval_minutes": 60,
    "sound": "1",
    "active": True,
    "last_reminder": None,
}


def get_dashboard_data():
    """Return saved values plus the totals used by the dashboard."""
    goal_glasses = water_data["goal_glasses"]
    glasses_drunk = water_data["water_count"]

    if goal_glasses:
        progress_percent = round(glasses_drunk / goal_glasses * 100)
    else:
        progress_percent = 0

    return {
        **water_data,
        "remaining_glasses": max(0, goal_glasses - glasses_drunk),
        "progress": min(100, progress_percent),
        "consumed_liters": round(glasses_drunk * 0.25, 2),
    }


@app.get("/")
def show_homepage():
    return render_template("index.html")


@app.get("/api/state")
def get_state():
    """Send the current dashboard values to the browser."""
    return jsonify(get_dashboard_data())


@app.post("/api/setup")
def save_setup():
    """Save the visitor's profile and calculate their daily water goal."""
    form_values = request.get_json(silent=True) or {}

    try:
        name = str(form_values.get("name", "")).strip()[:60]
        age = int(form_values.get("age"))
        weight_kg = float(form_values.get("weight"))
        interval_minutes = float(form_values.get("interval_minutes"))
        sound_choice = str(form_values.get("sound", "1"))

        valid_profile = name and age >= 1 and weight_kg > 0
        valid_interval = 1 <= interval_minutes <= 1440
        valid_sound = sound_choice in {"1", "2", "3"}
        if not (valid_profile and valid_interval and valid_sound):
            raise ValueError
    except (TypeError, ValueError):
        message = (
            "Enter a name, valid age and weight, an interval from 1 to 1440 "
            "minutes, and a sound choice."
        )
        return jsonify(error=message), 400

    goal_liters = daily_goal(weight_kg)
    water_data.update(
        name=name,
        age=age,
        weight=weight_kg,
        goal_liters=round(goal_liters, 2),
        goal_glasses=recommended_glasses(goal_liters),
        interval_minutes=interval_minutes,
        sound=sound_choice,
        water_count=0,
        missed_count=0,
        active=True,
        last_reminder=None,
    )
    return jsonify(get_dashboard_data())


@app.post("/api/water")
def add_water():
    """Add water in 250 ml glass increments."""
    form_values = request.get_json(silent=True) or {}

    try:
        amount_ml = int(form_values.get("amount_ml", 250))
        valid_amount = 250 <= amount_ml <= 5000 and amount_ml % 250 == 0
        if not valid_amount:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify(error="Amount must be a 250 ml increment, from 250 to 5000 ml."), 400

    glasses_to_add = amount_ml // 250
    new_count, missed_count, _, _ = record_drink(
        water_data["goal_glasses"],
        water_data["water_count"],
        water_data["missed_count"],
        drank_water=True,
    )

    # record_drink adds one glass; add any additional glasses from this entry.
    water_data["water_count"] = new_count + glasses_to_add - 1
    water_data["missed_count"] = missed_count

    # Stop reminders once the daily glass target has been reached.
    if water_data["water_count"] >= water_data["goal_glasses"]:
        water_data["active"] = False

    return jsonify(get_dashboard_data())


@app.post("/api/missed")
def record_missed_reminder():
    water_data["missed_count"] += 1
    return jsonify(get_dashboard_data())


@app.post("/api/reminded")
def record_reminder_time():
    water_data["last_reminder"] = datetime.now().strftime("%I:%M %p")
    return jsonify(get_dashboard_data())


@app.post("/api/reminder")
def update_reminder():
    """Pause or resume reminders and optionally change their interval."""
    form_values = request.get_json(silent=True) or {}
    requested_status = form_values.get("active", not water_data["active"])
    water_data["active"] = bool(requested_status)

    # Do not allow reminders to resume after the water goal is complete.
    goal_is_complete = (
        water_data["goal_glasses"] > 0
        and water_data["water_count"] >= water_data["goal_glasses"]
    )
    if goal_is_complete:
        water_data["active"] = False

    if "interval_minutes" in form_values:
        try:
            interval_minutes = float(form_values["interval_minutes"])
            if not 1 <= interval_minutes <= 1440:
                raise ValueError
            water_data["interval_minutes"] = interval_minutes
        except (TypeError, ValueError):
            return jsonify(error="Interval must be from 1 to 1440 minutes."), 400

    return jsonify(get_dashboard_data())


if __name__ == "__main__":
    app.run(debug=True)
