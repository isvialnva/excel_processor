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
        """

        """
        # Eliminar valores nulos para la detección
        series = series.dropna()

        # Si no hay datos, devolver string como predeterminado
        if len(series) == 0:
            return 'string'

        # Comprobar si son fechas
        try:
            if pd.api.types.is_datetime64_dtype(series):
                return 'datetime'

            # Intentar convertir a datetime
            pd.to_datetime(series, errors='raise')
            # Si algunas tienen hora, es datetime, sino es date
            if any(str(val).find(':') > 0 for val in series if not pd.isna(val)):
                return 'datetime'
            return 'date'
        except:
            pass

        # Comprobar si son booleanos
        if set(series.unique()) <= {True, False, 1, 0, '1', '0', 'yes', 'no', 'true', 'false', 'si', 'no'}:
            return 'boolean'

        # Comprobar si son enteros
        if pd.api.types.is_integer_dtype(series):
            return 'integer'

        # Intentar convertir a enteros
        try:
            series.astype(int)
            return 'integer'
        except:
            pass

        # Comprobar si son flotantes
        if pd.api.types.is_float_dtype(series):
            return 'float'

        # Intentar convertir a flotantes
        try:
            series.astype(float)
            return 'float'
        except:
            pass

        # Por defecto, tratar como texto
        return 'string'
