from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("excel_files/", include("excel_files.urls")),
    path("data_models/", include("data_models.urls")),
]
