# sabuzz/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile, JournalistRequest

User = get_user_model()

# ------------------------------------------------------------
# Create profile automatically for new users
# ------------------------------------------------------------
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(
            user=instance,
            role='user',  # default role
        )

# ------------------------------------------------------------
# Update profile automatically when user is saved
# ------------------------------------------------------------
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

# ------------------------------------------------------------
# Update role when JournalistRequest approved
# ------------------------------------------------------------
@receiver(post_save, sender=JournalistRequest)
def approve_journalist_request(sender, instance, **kwargs):
    if instance.status == 'approved':
        profile, created = Profile.objects.get_or_create(user=instance.user)
        profile.role = 'journalist'
        profile.full_name = instance.user.get_full_name() or instance.user.username
        profile.save()
