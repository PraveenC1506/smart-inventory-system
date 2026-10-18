from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Login and Logout
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='registration/login.html'
        ),
        name='login'
    ),
    path(
        'logout/',
        auth_views.LogoutView.as_view(),
        name='logout'
    ),

    # Existing application URLs
    path('', include('dashboard.urls')),
    path('products/', include('inventory.urls')),

    # REST API URLs
    path('api/', include('inventory.api_urls')),
]