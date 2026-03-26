from django.contrib.auth.models import User
from .models import Notification

def notify_admin(message, **kwargs):
    link = kwargs.get("link", "")

    admins = User.objects.filter(is_staff=True)

    for admin in admins:
        Notification.objects.create(
            recipient=admin,
            message=message,
            link=link
        )