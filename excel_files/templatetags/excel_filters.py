from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Obtiene un valor de un diccionario por su clave.
    Útil para acceder a diccionarios en plantillas.

    Uso en plantilla: {{ mi_diccionario|get_item:mi_clave }}
    """
    if dictionary is None:
        return None

    # Convierte key a string si es un entero, ya que en la plantilla se pasa como string
    return dictionary.get(str(key)) if isinstance(key, int) else dictionary.get(key)
