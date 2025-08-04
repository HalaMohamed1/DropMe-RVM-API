from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.root_welcome, name='root-welcome'),
    path('admin/', admin.site.urls),
    path('api/', include('recycling.urls')),
]
