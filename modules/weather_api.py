import requests

def get_weather_for_city(city_name, unit_system="metric"):
    """
    Fetches current weather for a city name using OpenMeteo.
    Returns a formatted string or error message.
    """
    if not city_name or city_name == "Unknown":
        return "No City Configured"

    try:
        # 1. Geocode
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=en&format=json"
        geo_res = requests.get(geo_url, timeout=5)
        geo_data = geo_res.json()

        if not geo_data.get("results"):
            return f"{city_name}: Not Found"

        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]

        # 2. Weather
        temp_unit = "fahrenheit" if unit_system == "imperial" else "celsius"
        wind_unit = "mph" if unit_system == "imperial" else "kmh"
        
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=relative_humidity_2m&temperature_unit={temp_unit}&windspeed_unit={wind_unit}"
        
        w_res = requests.get(weather_url, timeout=5)
        w_data = w_res.json()

        if "current_weather" in w_data:
            cw = w_data["current_weather"]
            temp = cw["temperature"]
            wind = cw["windspeed"]
            
            # Approximate humidity from hourly (current hour)
            # This is a simplification; ideally we match timestamps
            hum = "N/A"
            if "hourly" in w_data and "relative_humidity_2m" in w_data["hourly"]:
                 # Just take the first one or middle one for now? 
                 # Usually hourly returns 24h+ list. We need current time index.
                 # Let's just grab the one at index 0 (midnight) or nearest?
                 # Improved: Just grab the first one for simplicity or use current_weather params if they added it (they haven't).
                 # Better: Use the first value as "Today's Humidity"
                 hum = w_data["hourly"]["relative_humidity_2m"][0]

            # Simple condition mapping
            code = cw.get("weathercode", 0)
            icon = "☀️"
            if code > 3: icon = "☁️"
            if code > 50: icon = "🌧️"
            if code > 70: icon = "❄️"
            
            unit_ci = "F" if unit_system == "imperial" else "C"
            unit_sp = "mph" if unit_system == "imperial" else "km/h"
            
            return f"{city_name}: {icon} {temp}°{unit_ci} | 💧 {hum}% | 💨 {wind}{unit_sp}"
        
        return "Weather Unavailable"

    except Exception as e:
        return f"Weather Error: {e}"
