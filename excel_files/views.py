import logging
import traceback

from django.views.generic import CreateView, DetailView, ListView
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.db.models import Count
from excel_files.models import ExcelFile, ExcelSheet
from data_models.services.model_factory import DataModelFactory
from .services.file_manager import ExcelFileManager
from .services.schema_detector import SchemaDetector

logger = logging.getLogger(__name__)

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


class ExcelFileDetailView(DetailView):
    """
    Vista para mostrar los detalles de un archivo Excel, sus hojas y permitir
    procesar las hojas para crear tablas de datos.
    """
    model = ExcelFile
    template_name = 'excel_files/detail.html'
    context_object_name = 'excel_file'

    def get_context_data(self, **kwargs):
        """
        Agrega información adicional al contexto:
        - Hojas del archivo Excel
        - Tablas de datos generadas (si existen)
        """
        context = super().get_context_data(**kwargs)

        # Obtener hojas de Excel con sus columnas
        excel_file = self.get_object()
        sheets = ExcelSheet.objects.filter(excel_file=excel_file).prefetch_related('columns')
        context['sheets'] = sheets

        sheets = ExcelSheet.objects.filter(excel_file=excel_file).prefetch_related('columns')
        try:
            # Si hay una relación, intentar precargarla para evitar consultas N+1
            sheets = sheets.select_related('data_table')
        except:
            pass  # Si no existe la relación, ignorar este error

        context['sheets'] = sheets
        return context

    def post(self, request, *args, **kwargs):
        """
        Maneja las acciones POST para procesar una hoja específica
        y crear su tabla de datos correspondiente.
        """
        excel_file = self.get_object()
        sheet_id = request.POST.get('sheet_id')

        logger.debug(f"Iniciando procesamiento de hoja {sheet_id}")

        if not sheet_id:
            messages.error(request, 'No se especificó una hoja para procesar')
            return redirect('excel_files:detail', pk=excel_file.id)

        try:
            sheet = get_object_or_404(ExcelSheet, id=sheet_id, excel_file=excel_file)

            logger.info(f"Iniciando creación de tabla para hoja {sheet.id}: {sheet.name}")

            data_table = DataModelFactory.create_data_table_from_sheet(sheet.id)

            if data_table:
                logger.info(f"Tabla creada exitosamente: {data_table.table_name} con {data_table.row_count} filas")

                messages.success(
                    request,
                    f'Hoja "{sheet.name}" procesada exitosamente. '
                    f'Se generaron {data_table.row_count} filas de datos.'
                )
            else:
                logger.error(f"No se pudo crear la tabla de datos para la hoja {sheet.id}")
                messages.error(request, 'Error al procesar la hoja: no se pudo crear la tabla de datos')
        except Exception as e:
            logger.error(f"Error al procesar la hoja {sheet_id}: {str(e)}")
            logger.error(traceback.format_exc())
            messages.error(request, f'Error al procesar la hoja: {str(e)}')

        return redirect('excel_files:detail', pk=excel_file.id)


class ExcelFileListView(ListView):
    """
    Vista para mostrar la lista de archivos Excel subidos al sistema.
    Incluye información básica sobre cada archivo y opciones para gestionarlos.
    """
    model = ExcelFile
    template_name = 'excel_files/list.html'
    context_object_name = 'excel_files'
    paginate_by = 10  # Paginación para manejar muchos archivos
    ordering = ['-uploaded_at']  # Ordenar por fecha de subida, más recientes primero

    def get_queryset(self):
        """
        Obtiene la lista de archivos Excel con información adicional:
        - Número de hojas por archivo
        - Estado de procesamiento
        """
        queryset = super().get_queryset()
        # Añadir el conteo de hojas como anotación
        return queryset.annotate(sheet_count=Count('sheets'))

    def get_context_data(self, **kwargs):
        """
        Añade información adicional al contexto:
        - Filtros aplicados
        - Estadísticas generales
        """
        context = super().get_context_data(**kwargs)

        # Obtener filtros de la URL
        context['filter_processed'] = self.request.GET.get('processed', '')

        # Añadir estadísticas generales
        context['total_files'] = ExcelFile.objects.count()
        context['processed_files'] = ExcelFile.objects.filter(processed=True).count()
        context['pending_files'] = ExcelFile.objects.filter(processed=False).count()

        return context

    def post(self, request, *args, **kwargs):
        """
        Maneja acciones POST, como eliminar archivos o procesar sus hojas.
        """
        action = request.POST.get('action')
        file_id = request.POST.get('file_id')

        if not file_id:
            messages.error(request, 'No se especificó un archivo')
            return redirect('excel_files:list')

        try:
            excel_file = ExcelFile.objects.get(id=file_id)

            if action == 'delete':
                # Eliminar el archivo
                file_name = excel_file.name
                excel_file.delete()
                messages.success(request, f'Archivo "{file_name}" eliminado correctamente')

            elif action == 'process_sheets':
                # Procesar las hojas del archivo que no estén procesadas
                sheets = ExcelSheet.objects.filter(excel_file=excel_file, processed=False)
                for sheet in sheets:
                    try:
                        # Este método debería estar en tus servicios
                        from excel_files.services.schema_detector import SchemaDetector
                        SchemaDetector.detect_column_types(sheet.id)
                        sheet.processed = True
                        sheet.save()
                    except Exception as e:
                        messages.error(request, f'Error al procesar la hoja {sheet.name}: {str(e)}')

                # Verificar si todas las hojas están procesadas
                if not ExcelSheet.objects.filter(excel_file=excel_file, processed=False).exists():
                    excel_file.processed = True
                    excel_file.save()
                    messages.success(request, f'Todas las hojas del archivo "{excel_file.name}" fueron procesadas')
                else:
                    messages.warning(request, f'Algunas hojas no pudieron ser procesadas')

            elif action == 'refresh_sheets':
                # Volver a detectar las hojas del archivo
                try:
                    ExcelFileManager.read_excel_sheets(excel_file.id)
                    messages.success(request, f'Hojas del archivo "{excel_file.name}" actualizadas correctamente')
                except Exception as e:
                    messages.error(request, f'Error al actualizar las hojas: {str(e)}')

        except ExcelFile.DoesNotExist:
            messages.error(request, 'El archivo especificado no existe')
        except Exception as e:
            messages.error(request, f'Error al procesar la solicitud: {str(e)}')

        # Redirigir de vuelta a la lista
        return redirect('excel_files:list')