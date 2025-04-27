from django.urls import path
from .views import ExcelFileUploadView

urlpatterns = [
    path("excel_load/", ExcelFileUploadView.as_view(), name='ExcelFileUploadView'),
]