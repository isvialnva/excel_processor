import logging
import os
from django.shortcuts import render, get_object_or_404, redirect
from django.http import FileResponse
from django.conf import settings
from django.contrib import messages
from .models import DataTable
from .services.model_factory import DataModelFactory
from .services.export_service import ExportService

logger = logging.getLogger(__name__)

def view_table_data(request, table_id):
    """
    Vista para mostrar los datos de una tabla en formato tabular
    """
    data_table = get_object_or_404(DataTable, id=table_id)

    # Obtener número de página de la consulta
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 50))  # Ajusta según necesites

    # Usar el método existente para obtener los datos
    table_data = DataModelFactory.get_table_data(table_id, page, page_size)

    # Calcular total de páginas
    total_pages = (table_data['total_rows'] + page_size - 1) // page_size

    offset = (page - 1) * page_size

    context = {
        'data_table': data_table,
        'table_data': table_data,
        'current_page': page,
        'total_pages': total_pages,
        'page_size': page_size,
        'offset': offset
    }

    return render(request, 'data_models/view_table.html', context)


def export_table_parquet(request, table_id):
    """
    Vista para exportar una tabla de datos a formato Parquet

    Args:
        request: Objeto HttpRequest
        table_id: ID de la tabla a exportar

    Returns:
        FileResponse con el archivo Parquet para descargar o redirección a la vista de tabla
    """
    try:
        data_table = get_object_or_404(DataTable, id=table_id)

        # Exportar tabla a Parquet usando el servicio actualizado
        export_service = ExportService()
        export = export_service.export_to_parquet(table_id)

        # Determinar si se debe descargar el archivo o redirigir
        download = request.GET.get('download', 'true').lower() == 'true'

        if download:
            # Devolver el archivo como respuesta para descargar
            response = FileResponse(
                export.file.open('rb'),
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(export.file.name)}"'

            # Registrar la descarga
            logger.info(f"Usuario {request.user.username if request.user.is_authenticated else 'anónimo'} "
                        f"ha descargado la tabla {data_table.table_name} en formato Parquet")

            return response
        else:
            # Redirigir a la vista de tabla con mensaje de éxito
            messages.success(request,
                             f"Exportación a Parquet completada con éxito. El archivo está disponible en la sección 'Exportaciones previas'.")
            return redirect('data_models:view_table', table_id=table_id)

    except Exception as e:
        logger.error(f"Error al exportar tabla {table_id} a Parquet: {str(e)}")
        messages.error(request, f"Error al exportar tabla: {str(e)}")
        return redirect('data_models:view_table', table_id=table_id)
