from django.contrib import admin
from django.db import OperationalError, ProgrammingError
from django.http import HttpRequest, JsonResponse
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
# ViewSets are registered here as each app's views are built.


def health(request: HttpRequest) -> JsonResponse:
    from django.db import connection

    try:
        connection.ensure_connection()
        return JsonResponse({"status": "ok", "database": "ok"})
    except (OperationalError, ProgrammingError):
        return JsonResponse({"status": "error", "database": "unreachable"}, status=503)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    path("api/v1/", include(router.urls)),
    path("api/v1/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
