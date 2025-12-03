# sabuzz/templatetags/user_filters.py

from django import template

register = template.Library()

@register.filter
def is_journalist(user):
    """Check if the user is journalist or admin."""
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name="Journalists").exists()
