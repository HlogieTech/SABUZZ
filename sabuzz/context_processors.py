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
    return {"OPENWEATHER_API_KEY": settings.OPENWEATHER_API_KEY}
