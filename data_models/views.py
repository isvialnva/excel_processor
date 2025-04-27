from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import DataTable
from .services.model_factory import DataModelFactory


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