"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views


# Root URL → Login page
def home_redirect(request):
    return redirect('login')


urlpatterns = [
    path('', home_redirect),                     # ✅ FIX: root handled here
    path('admin/', admin.site.urls),

    # Accounts (login, dashboards)
    path('', include('accounts.urls')),
    path("api/accounts/", include("accounts.api_urls")),
    path("accounts/", include("accounts.urls")),
    path("api/trips/", include("trips.api_urls")),
    path("accounts/api/", include("trips.api_urls")),
 



    # App URLs
    path('trips/', include('trips.urls')),
    path('fuel/', include('fuel.urls')),

    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    
]

# Media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
