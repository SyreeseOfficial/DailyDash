import requests

def get_weather_for_city(city_name):
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
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        w_res = requests.get(weather_url, timeout=5)
        w_data = w_res.json()

        if "current_weather" in w_data:
            cw = w_data["current_weather"]
            temp = cw["temperature"]
            # OpenMeteo returns Celsius by default if unit not specified
            # We could handle unit conversion based on config passing, but to keep simple:
            # We'll assume C for now or check if we want F. API supports '&temperature_unit=fahrenheit'
            
            # Simple condition mapping
            code = cw.get("weathercode", 0)
            icon = "☀️"
            if code > 3: icon = "☁️"
            if code > 50: icon = "🌧️"
            if code > 70: icon = "❄️"
            
            return f"{city_name}: {icon} {temp}°C"
        
        return "Weather Unavailable"

    except Exception as e:
        return f"Weather Error: {e}"
