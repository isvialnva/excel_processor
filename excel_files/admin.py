from django.contrib import admin
from .models import ExcelFile, ExcelSheet, ColumnDefinition

admin.site.register(ExcelFile)
admin.site.register(ExcelSheet)
admin.site.register(ColumnDefinition)
