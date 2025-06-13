import json
import os

HISTORY_FILE = "watch_history.json"

# Initialize JSON file
def initialize_history():
    """Ensure JSON file exists and has the correct structure."""
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as file:
            json.dump({"short_videos": [], "long_videos": [], "points": 0}, file, indent=4)
    else:
        try:
            with open(HISTORY_FILE, "r") as file:
                data = json.load(file)
                if not isinstance(data, dict) or "short_videos" not in data or "long_videos" not in data or "points" not in data:
                    raise ValueError
        except (json.JSONDecodeError, ValueError):
            with open(HISTORY_FILE, "w") as file:
                json.dump({"short_videos": [], "long_videos": [], "points": 0}, file, indent=4)

# Save a video and update points
def save_history(video_type, video_name):
    """Save a video and award points based on type."""
    with open(HISTORY_FILE, "r") as file:
        data = json.load(file)

    points = 5 if video_type == "short_videos" else 10  # Points per video
    data[video_type].append(video_name)
    data["points"] += points  # Add points

    with open(HISTORY_FILE, "w") as file:
        json.dump(data, file, indent=4)
    
    return points  # Return points awarded

# Display history
def display_history():
    """Return stored history and points."""
    with open(HISTORY_FILE, "r") as file:
        return json.load(file)

# Reset points
def reset_points():
    """Reset the points to zero."""
    with open(HISTORY_FILE, "r") as file:
        data = json.load(file)

    data["points"] = 0  # Reset points
    with open(HISTORY_FILE, "w") as file:
        json.dump(data, file, indent=4)
    
    return True

# Initialize JSON on import
initialize_history()
