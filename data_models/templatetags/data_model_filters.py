from django import template
from datetime import date, datetime
import decimal

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Obtiene un valor de un diccionario por su clave.
    """
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def get_range(value):
    """
    Genera un rango de números del 1 al valor dado.
    """
    return range(1, value + 1)


@register.filter
def format_cell_value(row, column):
    """
    Formatea el valor de una celda según el tipo de datos de la columna.
    """
    if row is None or column is None:
        return ""

    value = row.get(column['name'])
    if value is None:
        return ""

    # Formatear según el tipo de datos
    data_type = column.get('type', 'string')

    if data_type == 'integer':
        # Asegurar que se muestre como número entero
        try:
            return str(int(value))
        except (ValueError, TypeError):
            return str(value)

    elif data_type == 'float':
        # Formatear decimales con dos lugares
        try:
            if isinstance(value, (int, float, decimal.Decimal)):
                return f"{float(value):.2f}"
            return str(value)
        except (ValueError, TypeError):
            return str(value)
