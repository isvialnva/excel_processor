from django import template

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