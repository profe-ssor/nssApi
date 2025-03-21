from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include, re_path
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('digital360Api.urls')),
    path('favicon.ico', lambda request: HttpResponse(status=204)),
]

@api_view(['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def not_found(request, *args, **kwargs):
    return Response(
        {"error": "The requested resource was not found."},
        status=status.HTTP_404_NOT_FOUND
    )

# Add this at the end of your urlpatterns
urlpatterns += [
    # Catch-all pattern for API routes
    re_path(r'^api/.*$', not_found),
]