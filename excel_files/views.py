from django.shortcuts import render, redirect, reverse
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView
from .models import ExcelFile, ExcelSheet
from .services.file_manager import ExcelFileManager
from .services.schema_detector import SchemaDetector


class ExcelFileUploadView(CreateView):
    model = ExcelFile
    template_name = 'excel_files/upload.html'
    fields = ['name', 'description', 'file']

    def form_valid(self, form):
        response = super().form_valid(form)

        try:
            # Procesar las hojas del archivo
            sheets = ExcelFileManager.read_excel_sheets(self.object.id)

            # Detectar tipos de columnas para cada hoja
            for sheet in sheets:
                SchemaDetector.detect_column_types(sheet.id)

            messages.success(self.request, f'Archivo "{self.object.name}" procesado con éxito')
        except Exception as e:
            messages.error(self.request, f'Error al procesar el archivo: {str(e)}')

        return response

    def get_success_url(self):
        return reverse('excel_files:detail', kwargs={'pk': self.object.pk})
