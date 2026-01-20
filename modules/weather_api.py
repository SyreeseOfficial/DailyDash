import requests
import time
import threading

# Cache Globals
_weather_cache = {
    "city": None,
    "unit_system": None,
    "data": None,
    "timestamp": 0
}

_is_fetching = False

def get_weather_for_city(city_name, unit_system="metric"):
    """
    Fetches current weather for a city name using OpenMeteo.
    Returns a formatted string.
    Uses usage-based caching (15 min) and background fetching to avoid UI blocking.
    """
    global _is_fetching

    if not city_name or city_name == "Unknown":
        return "No City Configured"

    current_time = time.time()
    
    # 1. Check if we have valid cache
    if (_weather_cache["city"] == city_name and 
        _weather_cache["unit_system"] == unit_system and 
        _weather_cache["data"] is not None):
        
        age = current_time - _weather_cache["timestamp"]
        if age < 900: # 15 min expiration
            return _weather_cache["data"]

    # 2. If valid cache missing or stale, trigger background update
    if not _is_fetching:
        _is_fetching = True
        t = threading.Thread(target=_fetch_weather_thread, args=(city_name, unit_system))
        t.daemon = True
        t.start()

    # 3. Return what we have
    if _weather_cache["data"]:
        return _weather_cache["data"] # Return stale data while updating
    
    return "Weather: Loading..."

def _fetch_weather_thread(city_name, unit_system):
    """
    Background worker to perform the network request.
    """
    global _is_fetching
    
    try:
        # 1. Geocode
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=en&format=json"
        geo_res = requests.get(geo_url, timeout=10)
        geo_data = geo_res.json()

        if not geo_data.get("results"):
            _weather_cache["data"] = f"{city_name}: Not Found"
            return

        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]

        # 2. Weather
        temp_unit = "fahrenheit" if unit_system == "imperial" else "celsius"
        wind_unit = "mph" if unit_system == "imperial" else "kmh"
        
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=relative_humidity_2m&temperature_unit={temp_unit}&windspeed_unit={wind_unit}"
        
        w_res = requests.get(weather_url, timeout=10)
        w_data = w_res.json()

        if "current_weather" in w_data:
            cw = w_data["current_weather"]
            temp = cw["temperature"]
            wind = cw["windspeed"]
            
            # Approximate humidity from hourly (current hour)
            hum = "N/A"
            if "hourly" in w_data and "relative_humidity_2m" in w_data["hourly"]:
                 hum = w_data["hourly"]["relative_humidity_2m"][0]

            # Simple condition mapping
            code = cw.get("weathercode", 0)
            icon = ":sunny:" # Rich markup
            if code > 3: icon = ":cloud:" 
            if code > 50: icon = ":cloud_with_rain:"
            if code > 70: icon = ":snowflake:"
            
            unit_ci = "F" if unit_system == "imperial" else "C"
            unit_sp = "mph" if unit_system == "imperial" else "km/h"
            
            result = f"{city_name}: {icon}  {temp}°{unit_ci} | :droplet: {hum}% | :dash: {wind}{unit_sp}"
            
            # Update Cache
            _weather_cache["city"] = city_name
            _weather_cache["unit_system"] = unit_system
            _weather_cache["data"] = result
            _weather_cache["timestamp"] = time.time()
            
    except Exception as e:
        # In case of error, we don't update data (keep old if leaks), or set error if None
        if _weather_cache["data"] is None:
             _weather_cache["data"] = "Weather: Connection Error"
    finally:
        _is_fetching = False
