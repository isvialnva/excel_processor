import pandas as pd
from django.utils.text import slugify
from excel_files.models import ExcelSheet, ColumnDefinition
import re


class SchemaDetector:
    """
    
    """

    @staticmethod
    def detect_column_types(sheet_id):
        """

        """

        sheet = ExcelSheet.objects.get(id=sheet_id)
        df = pd.read_excel(sheet.excel_file.file.path, sheet_name=sheet.name)

        columns = []
        for i, col_name in enumerate(df.columns):
            # Normalizar nombre de columna
            normalized_name = SchemaDetector._normalize_column_name(col_name)

            # Detectar tipo de datos
            data_type = SchemaDetector._detect_data_type(df[col_name])

            # Verificar si hay valores nulos
            nullable = df[col_name].isnull().any()

            # Crear o actualizar definición de columna
            col_def, created = ColumnDefinition.objects.update_or_create(
                sheet=sheet,
                column_index=i,
                defaults={
                    'name': normalized_name,
                    'original_name': str(col_name),
                    'data_type': data_type,
                    'nullable': nullable
                }
            )
            columns.append(col_def)

        return columns

    @staticmethod
    def _normalize_column_name(col_name):
        """

        """
        # Convertir a string si no lo es
        col_name = str(col_name)

        # Eliminar caracteres especiales y espacios
        normalized = re.sub(r'[^\w\s]', '', col_name)

        # Convertir a snake_case
        normalized = slugify(normalized).replace('-', '_')

        # Asegurar que no empiece con número
        if normalized and normalized[0].isdigit():
            normalized = f"col_{normalized}"

        # Si está vacío, usar un nombre genérico
        if not normalized:
            normalized = "unnamed_column"

        return normalized

    @staticmethod
    def _detect_data_type(series):
        """Detecta el tipo de datos de una serie de pandas."""
        # Eliminar valores nulos para la detección
        series = series.dropna()

        # Si no hay datos, devolver string como predeterminado
        if len(series) == 0:
            return 'string'

        # Primero verificar si son enteros o flotantes
        if pd.api.types.is_integer_dtype(series):
            return 'integer'

        if pd.api.types.is_float_dtype(series):
            return 'float'

        # Verificar booleanos
        if set(series.unique()) <= {True, False, 1, 0, '1', '0', 'yes', 'no', 'true', 'false', 'si', 'no'}:
            return 'boolean'

        # Intentar convertir a enteros si no es ya un tipo numérico
        try:
            # Si todos los valores pueden convertirse a enteros sin pérdida
            integers = series.astype(int)
            if (integers == series).all():
                return 'integer'
        except:
            pass

        # Intentar convertir a flotantes
        try:
            series.astype(float)
            return 'float'
        except:
            pass

        # Verificar si tienen formato de fecha
        # Primero, comprobar si los valores tienen patrones típicos de fechas
        date_patterns = [
            r'\d{1,4}[-/]\d{1,2}[-/]\d{1,4}',  # 2023-04-25, 04/25/2023, etc.
            r'\d{1,2}[-/]\s*[a-zA-Z]{3,9}[-/]\s*\d{2,4}',  # 25-Apr-2023, etc.
        ]

        sample_size = min(20, len(series))
        sample = series.sample(sample_size) if len(series) > sample_size else series

        # Verificar si al menos el 80% de la muestra tiene formato de fecha
        date_like_count = sum(1 for val in sample if any(re.search(pattern, str(val)) for pattern in date_patterns))
        if date_like_count >= sample_size * 0.8:
            try:
                # Ahora intentar convertir a datetime
                pd.to_datetime(series, errors='raise')
                # Si algunas tienen hora, es datetime, sino es date
                if any(str(val).find(':') > 0 for val in series if not pd.isna(val)):
                    return 'datetime'
                return 'date'
            except:
                pass

        # Si es un tipo datetime conocido
        if pd.api.types.is_datetime64_dtype(series):
            return 'datetime'

        # Por defecto, tratar como texto
        return 'string'
