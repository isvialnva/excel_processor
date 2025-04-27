import logging
import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from django.conf import settings
from django.utils import timezone
from django.core.files.base import ContentFile
from data_models.models import DataTable, TableExport
from excel_files.models import ColumnDefinition

logger = logging.getLogger(__name__)


class ExportService:
    """Servicio para exportar datos a diferentes formatos"""

    @staticmethod
    def export_to_parquet(data_table_id, file_path=None):
        """
        Exporta una tabla de datos a un archivo Parquet y lo guarda en el modelo TableExport

        Args:
            data_table_id: ID de la tabla de datos a exportar
            file_path: Ruta donde guardar el archivo. Si es None, se genera una automáticamente

        Returns:
            TableExport: Objeto de exportación creado
        """
        try:
            data_table = DataTable.objects.get(id=data_table_id)
            sheet = data_table.sheet

            # Crear directorio de exportación si no existe
            export_dir = os.path.join(settings.MEDIA_ROOT, 'EXPORTS', 'PARQUET')
            os.makedirs(export_dir, exist_ok=True)

            # Generar nombre de archivo si no se proporciona
            if not file_path:
                timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
                safe_name = data_table.table_name.replace(" ", "_").lower()
                file_name = f"{safe_name}_{timestamp}.parquet"
                file_path = os.path.join(export_dir, file_name)

            # Obtener definiciones de columnas
            columns = list(ColumnDefinition.objects.filter(sheet=sheet).order_by('column_index'))
            column_names = [col.name for col in columns]
            column_types = {col.name: col.data_type for col in columns}

            # Crear DataFrame vacío con las columnas definidas
            df = pd.DataFrame(columns=column_names)

            # Procesar datos por lotes para evitar problemas de memoria
            batch_size = 1000
            total_batches = (data_table.row_count + batch_size - 1) // batch_size

            logger.info(f"Iniciando exportación a Parquet para tabla {data_table.table_name}")
            logger.info(f"Total de filas: {data_table.row_count}")
            logger.info(f"Procesando en {total_batches} lotes de {batch_size} filas")

            # Procesar filas por lotes
            from django.db import connection

            # Optimizar la consulta SQL directamente para mejor rendimiento
            query = """
                SELECT r.row_index, cd.name, 
                    CASE cd.data_type
                        WHEN 'string' THEN c.string_value
                        WHEN 'integer' THEN CAST(c.integer_value AS TEXT)
                        WHEN 'float' THEN CAST(c.float_value AS TEXT)
                        WHEN 'date' THEN CAST(c.date_value AS TEXT)
                        WHEN 'datetime' THEN CAST(c.datetime_value AS TEXT)
                        WHEN 'boolean' THEN CAST(c.boolean_value AS TEXT)
                    END as value
                FROM data_models_datarow r
                JOIN data_models_datacell c ON c.row_id = r.id
                JOIN excel_files_columndefinition cd ON cd.id = c.column_definition_id
                WHERE r.table_id = %s
                ORDER BY r.row_index, cd.column_index
            """

            with connection.cursor() as cursor:
                cursor.execute(query, [data_table_id])

                # Crear un diccionario para almacenar los datos por filas
                all_rows = {}

                # Procesar resultados
                for row_index, col_name, value in cursor.fetchall():
                    if row_index not in all_rows:
                        all_rows[row_index] = {}

                    # Convertir valor según el tipo de datos
                    if value is not None:
                        data_type = column_types.get(col_name)
                        if data_type == 'integer':
                            try:
                                value = int(value)
                            except (ValueError, TypeError):
                                pass
                        elif data_type == 'float':
                            try:
                                value = float(value)
                            except (ValueError, TypeError):
                                pass
                        elif data_type == 'boolean':
                            value = value.lower() in ('true', 'yes', 'si', '1', 'verdadero')

                    all_rows[row_index][col_name] = value

            # Convertir a DataFrame
            df = pd.DataFrame.from_dict(all_rows, orient='index')
            df = df.reset_index(drop=True)

            # Convertir tipos de datos apropiados
            for col_name, data_type in column_types.items():
                if col_name in df.columns:
                    if data_type == 'integer':
                        df[col_name] = pd.to_numeric(df[col_name], errors='coerce').astype('Int64')
                    elif data_type == 'float':
                        df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
                    elif data_type == 'date':
                        df[col_name] = pd.to_datetime(df[col_name], errors='coerce').dt.date
                    elif data_type == 'datetime':
                        df[col_name] = pd.to_datetime(df[col_name], errors='coerce')
                    elif data_type == 'boolean':
                        df[col_name] = df[col_name].astype('boolean')

            # Guardar como Parquet
            table = pa.Table.from_pandas(df)
            pq.write_table(table, file_path)

            # Obtener tamaño del archivo
            file_size = os.path.getsize(file_path)

            # Crear registro en TableExport
            with open(file_path, 'rb') as f:
                export = TableExport(
                    table=data_table,
                    format='parquet',
                    file_size=file_size
                )
                export.file.save(os.path.basename(file_path), ContentFile(f.read()))

            logger.info(f"Archivo Parquet generado exitosamente: {file_path}")
            logger.info(f"Exportación registrada con ID: {export.id}")

            return export

        except Exception as e:
            logger.error(f"Error al exportar tabla {data_table_id} a Parquet: {str(e)}")
            logger.exception(e)
            raise
