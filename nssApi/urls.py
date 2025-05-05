from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include, re_path
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('digital360Api.urls')),
    path('nss_personnel/', include('nss_personnel.urls')),
    path('nss_supervisor/', include('nss_supervisors.urls')),
    path('nss_admin/', include('nss_admin.urls')),
    path('file_uploads/', include('file_uploads.urls')),
    path('messageApp/', include('messageApp.urls')),
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

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

