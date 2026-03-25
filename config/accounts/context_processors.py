from .models import Notification

def admin_notifications(request):
    if request.user.is_authenticated and request.user.is_staff:
        notifications = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        )[:100]
        return {
            "notifications": notifications,
            "notification_count": notifications.count()
        }
    return {}
