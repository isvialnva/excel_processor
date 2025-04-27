import logging
import pandas as pd
from data_models.models import DataTable, DataRow, DataCell
from excel_files.models import ExcelSheet, ColumnDefinition
from django.db import transaction
import traceback

logger = logging.getLogger(__name__)


class DataModelFactory:
    """Factory para crear y poblar modelos de datos dinámicos"""

    @staticmethod
    @transaction.atomic
    def create_data_table_from_sheet(sheet_id, batch_size=1000):
        """
        Crea una tabla de datos a partir de una hoja de Excel

        Args:
            sheet_id: ID de la hoja de Excel
            batch_size: Tamaño del lote para procesar filas

        Returns:
            DataTable: Instancia de la tabla de datos creada
        """
        try:
            sheet = ExcelSheet.objects.select_related('excel_file').get(id=sheet_id)

            # Verificar que la hoja tenga definiciones de columnas
            if not ColumnDefinition.objects.filter(sheet=sheet).exists():
                raise ValueError(f"La hoja {sheet.name} no tiene definiciones de columnas")

            # Crear o actualizar la tabla de datos
            table_name = f"{sheet.excel_file.id}_{sheet.name}"
            data_table, created = DataTable.objects.update_or_create(
                sheet=sheet,
                defaults={'table_name': table_name}
            )

            # Obtener DataFrame
            df = pd.read_excel(sheet.excel_file.file.path, sheet_name=sheet.name)

            # Obtener columnas definidas
            columns = list(ColumnDefinition.objects.filter(sheet=sheet).order_by('column_index'))

            # Procesar por lotes para evitar problemas de memoria
            total_rows = len(df)
            data_table.row_count = total_rows
            data_table.save()

            # Eliminar filas existentes si no es una creación nueva
            if not created:
                DataRow.objects.filter(table=data_table).delete()

            # Procesar las filas en lotes
            for start_idx in range(0, total_rows, batch_size):
                end_idx = min(start_idx + batch_size, total_rows)
                batch_df = df.iloc[start_idx:end_idx]

                with transaction.atomic():
                    DataModelFactory._process_batch(data_table, batch_df, columns, start_idx)

            # Marcar la hoja como procesada
            sheet.processed = True
            sheet.save()

            # Marcar el archivo como procesado si todas sus hojas están procesadas
            if not ExcelSheet.objects.filter(excel_file=sheet.excel_file, processed=False).exists():
                sheet.excel_file.processed = True
                sheet.excel_file.save()

            return data_table
        except Exception as e:
            logger.error(f"Error al crear tabla de datos para hoja {sheet_id}: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    @staticmethod
    def _process_batch(data_table, batch_df, columns, start_idx):
        """
        Procesa un lote de filas

        Args:
            data_table: Tabla de datos
            batch_df: DataFrame con el lote de datos
            columns: Lista de definiciones de columnas
            start_idx: Índice de inicio para este lote
        """
        # Crear filas
        data_rows = []
        for i in range(len(batch_df)):
            data_rows.append(DataRow(
                table=data_table,
                row_index=start_idx + i
            ))

        # Insertar filas en la base de datos
        data_rows = DataRow.objects.bulk_create(data_rows)

        # Crear celdas
        data_cells = []
        for i, row in enumerate(data_rows):
            df_row = batch_df.iloc[i]

            for col in columns:
                # Obtener valor original, usando el nombre original de la columna
                original_value = df_row.get(col.original_name)

                # Crear celda con el valor adecuado según el tipo de datos
                cell = DataCell(row=row, column_definition=col)

                # Asignar valor según tipo
                if pd.isna(original_value):
                    pass  # Dejar como NULL
                elif col.data_type == 'string':
                    cell.string_value = str(original_value)
                elif col.data_type == 'integer':
                    try:
                        cell.integer_value = int(original_value)
                    except (ValueError, TypeError):
                        cell.string_value = str(original_value)
                elif col.data_type == 'float':
                    try:
                        cell.float_value = float(original_value)
                    except (ValueError, TypeError):
                        cell.string_value = str(original_value)
                elif col.data_type == 'date':
                    try:
                        cell.date_value = pd.to_datetime(original_value).date()
                    except:
                        cell.string_value = str(original_value)
                elif col.data_type == 'datetime':
                    try:
                        cell.datetime_value = pd.to_datetime(original_value)
                    except:
                        cell.string_value = str(original_value)
                elif col.data_type == 'boolean':
                    # Manejar varios formatos de booleano
                    bool_value = False
                    if isinstance(original_value, bool):
                        bool_value = original_value
                    elif isinstance(original_value, (int, float)):
                        bool_value = original_value > 0
                    elif isinstance(original_value, str):
                        bool_value = original_value.lower() in ('true', 'yes', 'si', '1', 'verdadero')
                    cell.boolean_value = bool_value

                data_cells.append(cell)

        # Insertar celdas en la base de datos
        DataCell.objects.bulk_create(data_cells)

    @staticmethod
    def get_table_data(data_table_id, page=1, page_size=100):
        """
        Obtiene los datos de una tabla en formato estructurado

        Args:
            data_table_id: ID de la tabla de datos
            page: Número de página
            page_size: Tamaño de página

        Returns:
            dict: Datos estructurados con columnas y filas
        """
        try:
            data_table = DataTable.objects.get(id=data_table_id)
            sheet = data_table.sheet

            # Obtener definiciones de columnas
            columns = list(ColumnDefinition.objects.filter(sheet=sheet).order_by('column_index'))

            # Calcular offset para paginación
            offset = (page - 1) * page_size

            # Obtener filas para la página actual
            rows = DataRow.objects.filter(table=data_table).order_by('row_index')[offset:offset + page_size]

            # Preparar estructura de resultados
            result = {
                'table_name': data_table.table_name,
                'total_rows': data_table.row_count,
                'page': page,
                'page_size': page_size,
                'columns': [{'name': col.name, 'original_name': col.original_name, 'type': col.data_type} for col in
                            columns],
                'rows': []
            }

            # Para cada fila, obtener todas sus celdas
            for row in rows:
                cells = DataCell.objects.filter(row=row).select_related('column_definition')
                row_data = {}

                for cell in cells:
                    row_data[cell.column_definition.name] = cell.get_value()

                result['rows'].append(row_data)

            return result
        except Exception as e:
            logger.error(f"Error al obtener datos de tabla {data_table_id}: {str(e)}")
            logger.error(traceback.format_exc())
            raise
