from django.urls import path
from .views import ExcelFileUploadView, ExcelFileDetailView, ExcelFileListView

app_name = "excel_files"

urlpatterns = [
    path('upload/', ExcelFileUploadView.as_view(), name='upload'),
    path('<int:pk>/', ExcelFileDetailView.as_view(), name='detail'),
    path('list/', ExcelFileListView.as_view(), name='list'),
]