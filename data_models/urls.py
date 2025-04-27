from django.urls import path
from . import views

app_name = "data_models"

urlpatterns = [
    path('table/<int:table_id>/', views.view_table_data, name='view_table'),
    path('table/<int:table_id>/export/parquet/', views.export_table_parquet, name='export_parquet')
]