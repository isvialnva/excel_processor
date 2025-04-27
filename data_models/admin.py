from django.contrib import admin
from .models import DataTable, DataRow, DataCell, TableExport

admin.site.register(DataTable)
admin.site.register(DataRow)
admin.site.register(DataCell)
admin.site.register(TableExport)