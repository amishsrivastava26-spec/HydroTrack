"""Water goal calculations and the original console reminder functions."""

import time


def daily_goal(weight_kg):
    """Calculate the daily water goal using the original 0.033 L/kg rule."""
    return float(weight_kg) * 0.033


def recommended_glasses(goal_liters):
    """Convert the water goal into 250 ml glasses."""
    return round(float(goal_liters) / 0.25)


def record_drink(glass_goal, glasses_drunk, missed_glasses, drank_water):
    """Update the consumed and missed glass totals by one glass."""
    if drank_water:
        glasses_drunk += 1
    else:
        missed_glasses += 1

    glasses_left = max(0, glass_goal - glasses_drunk)
    if glass_goal:
        progress_percent = glasses_drunk / glass_goal * 100
    else:
        progress_percent = 100

    return glasses_drunk, missed_glasses, glasses_left, progress_percent


def play_sound(sound_choice):
    """Play one of the original beep tones on Windows, if available."""
    try:
        import winsound
    except ImportError:
        return False

    sound_frequencies = {"1": 1000, "2": 2000, "3": 3000}
    frequency = sound_frequencies.get(str(sound_choice))
    if frequency is None:
        return False

    winsound.Beep(frequency, 500)
    return True


def set_reminder(sound_choice):
    """Show the original desktop notification and play its selected sound."""
    try:
        from plyer import notification

        notification.notify(
            title="Plz drink some water",
            message="You need to drink some water now!!",
            timeout=10,
        )
    except (ImportError, RuntimeError):
        # Desktop notifications may not be available on every computer.
        pass

    play_sound(sound_choice)


def records(glass_goal, glasses_drunk, missed_glasses):
    """Ask the original console question and print the updated totals."""
    answer = input("Do you drink water? Y/N")
    drank_water = answer.upper() == "Y"

    glasses_drunk, missed_glasses, glasses_left, progress_percent = record_drink(
        glass_goal, glasses_drunk, missed_glasses, drank_water
    )

    print("Details:")
    print("Glasses consumed:", glasses_drunk)
    print("Missed glasses:", missed_glasses)

    if glasses_drunk >= glass_goal:
        print("Congratulations! Goal achieved.")
    else:
        print(f"{glasses_left} glasses remaining to reach your goal")
        print(f"Progress: {progress_percent}%")

    return glasses_drunk, missed_glasses


def set_timer(wait_seconds, glass_goal, glasses_drunk, missed_glasses, sound_choice):
    """Wait between reminders and ask whether the user drank water."""
    while True:
        time.sleep(wait_seconds)
        set_reminder(sound_choice)
        glasses_drunk, missed_glasses = records(
            glass_goal, glasses_drunk, missed_glasses
        )


def main(name):
    """Run the original console setup when this function is called directly."""
    print(f"Hello, {name}!")

    age = int(input("Enter your age: "))
    weight_kg = float(input("Enter your weight in kg: "))

    goal_liters = daily_goal(weight_kg)
    glass_goal = recommended_glasses(goal_liters)
    print(f"Recommended water goal: {goal_liters:.2f} liters")
    print(f"We recommend {glass_goal} glasses of water each day.")

    interval_minutes = float(input("Enter reminder interval in minutes: "))
    wait_seconds = interval_minutes * 60
    sound_choice = input(
        "Choose notification sound:\n"
        "1 for Low Beep\n"
        "2 for Medium Beep\n"
        "3 for High Beep\n"
        "Enter number: "
    )

    set_timer(wait_seconds, glass_goal, 0, 0, sound_choice)
