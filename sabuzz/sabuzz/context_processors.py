import requests
# sabuzz/context_processors.py
from .views import is_journalist as is_journalist_check # pyright: ignore[reportMissingImports]

def user_roles(request):
    """
    Adds is_journalist boolean to all template contexts.
    """
    user = getattr(request, "user", None)
    try:
        is_journalist = bool(user and user.is_authenticated and is_journalist_check(user))
    except Exception:
        is_journalist = False

    return {
        "is_journalist": is_journalist
    }

def global_weather(request):
    """Provides global weather data for the navbar."""

    lat = -26.2041
    lon = 28.0473

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current_weather=true"
        f"&timezone=Africa/Johannesburg"
    )


    weather = {}

    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        current = data.get("current_weather", {})

        if current:
            weather = {
                "temperature": current.get("temperature"),
                "windspeed": current.get("windspeed"),
            }
    except:
        weather = None

    return {"global_weather": weather}
