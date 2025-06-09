# Define extended seasonal phases for 3-day representation of each season
# Each sub-season (Early, Mid, Late) has slightly different characteristics
import json
import random

seasonal_phases = [
    ("Early Spring", {"base_temp_day": 10, "base_temp_night": 3, "humidity": (55, 70), "rain": (0, 1), "snow": (0, 0), "wind_speed": (1, 3), "uvi": (2, 4), "desc": "scattered clouds"}),
    ("Mid Spring", {"base_temp_day": 16, "base_temp_night": 8, "humidity": (50, 65), "rain": (0, 2), "snow": (0, 0), "wind_speed": (1, 3), "uvi": (3, 5), "desc": "clear sky"}),
    ("Late Spring", {"base_temp_day": 21, "base_temp_night": 13, "humidity": (50, 70), "rain": (0, 3), "snow": (0, 0), "wind_speed": (2, 4), "uvi": (4, 6), "desc": "light rain"}),

    ("Early Summer", {"base_temp_day": 26, "base_temp_night": 18, "humidity": (60, 80), "rain": (1, 4), "snow": (0, 0), "wind_speed": (1, 3), "uvi": (6, 8), "desc": "sunny"}),
    ("Mid Summer", {"base_temp_day": 31, "base_temp_night": 24, "humidity": (70, 90), "rain": (2, 6), "snow": (0, 0), "wind_speed": (2, 5), "uvi": (8, 11), "desc": "thunderstorm"}),
    ("Late Summer", {"base_temp_day": 28, "base_temp_night": 21, "humidity": (65, 85), "rain": (1, 5), "snow": (0, 0), "wind_speed": (1, 4), "uvi": (7, 10), "desc": "hot"}),

    ("Early Fall", {"base_temp_day": 23, "base_temp_night": 15, "humidity": (55, 75), "rain": (0, 2), "snow": (0, 0), "wind_speed": (1, 3), "uvi": (3, 5), "desc": "clear sky"}),
    ("Mid Fall", {"base_temp_day": 17, "base_temp_night": 10, "humidity": (50, 70), "rain": (0, 1), "snow": (0, 0), "wind_speed": (1, 3), "uvi": (2, 4), "desc": "overcast clouds"}),
    ("Late Fall", {"base_temp_day": 11, "base_temp_night": 3, "humidity": (45, 65), "rain": (0, 1), "snow": (0, 0.2), "wind_speed": (2, 4), "uvi": (1, 3), "desc": "light rain"}),

    ("Early Winter", {"base_temp_day": 4, "base_temp_night": -4, "humidity": (40, 60), "rain": (0, 0), "snow": (0.5, 1.5), "wind_speed": (2, 4), "uvi": (0, 1), "desc": "light snow"}),
    ("Mid Winter", {"base_temp_day": -1, "base_temp_night": -8, "humidity": (35, 55), "rain": (0, 0), "snow": (1, 2.5), "wind_speed": (2, 5), "uvi": (0, 1), "desc": "snow"}),
    ("Late Winter", {"base_temp_day": 3, "base_temp_night": -3, "humidity": (40, 60), "rain": (0, 0), "snow": (0.5, 2), "wind_speed": (2, 4), "uvi": (1, 2), "desc": "overcast clouds"})
]

# Initialize JSON structure
extended_weather_json = {
    "city": "samplecity",
    "hourly": []
}

# Generate data
hour_index = 0
for season_name, props in seasonal_phases:
    for h in range(24):
        is_daytime = 7 <= h <= 18
        temp_base = props["base_temp_day"] if is_daytime else props["base_temp_night"]
        temp = round(temp_base + random.uniform(-1.5, 1.5), 1)
        humidity = random.randint(*props["humidity"])
        rain = round(random.uniform(*props["rain"]), 1)
        snow = round(random.uniform(*props["snow"]), 1)
        wind_speed = round(random.uniform(*props["wind_speed"]), 1)
        wind_deg = random.randint(0, 359)
        uvi = round(random.uniform(*props["uvi"]), 1) if is_daytime else 0
        desc = props["desc"]

        extended_weather_json["hourly"].append({
            "hour": hour_index,
            "temp": temp,
            "humidity": humidity,
            "rain": rain,
            "snow": snow,
            "wind_speed": wind_speed,
            "wind_deg": wind_deg,
            "uvi": uvi,
            "weather": [{"description": desc}]
        })
        hour_index += 1

# Save JSON file
output_path = "data/samplecity.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(extended_weather_json, f, ensure_ascii=False, indent=2)

output_path
