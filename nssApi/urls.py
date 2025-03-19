from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('digital360Api.urls')),
    path('favicon.ico', lambda request: HttpResponse(status=204)),
]