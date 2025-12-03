# sabuzz/context_processors.py
import requests
from django.conf import settings

def user_roles(request):
    """
    Adds is_journalist boolean to all templates.
    Avoids importing views to prevent circular imports.
    """
    user = getattr(request, "user", None)
    try:
        is_journalist = bool(
            user and user.is_authenticated and (
                user.is_superuser or user.groups.filter(name="Journalists").exists()
            )
        )
    except Exception:
        is_journalist = False

    return {"is_journalist": is_journalist}


def global_weather(request):
    """
    Minimal, defensive weather context processor.
    Returns 'global_weather' dict used by navbar (or None on failure).
    """
    lat = -26.2041
    lon = 28.0473

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current_weather=true"
        f"&timezone=Africa/Johannesburg"
    )

    gw = None
    try:
        r = requests.get(url, timeout=3)
        r.raise_for_status()
        data = r.json()
        current = data.get("current_weather") or {}
        # provide a tiny, safe object for templates
        gw = {
            "temperature": current.get("temperature"),
            "windspeed": current.get("windspeed"),
        }
    except Exception:
        gw = None

    return {"global_weather": gw}
