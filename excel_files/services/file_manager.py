import pandas as pd
import logging
from excel_files.models import ExcelFile, ExcelSheet
import traceback

logger = logging.getLogger(__name__)


class ExcelFileManager:
    """

    """

    @staticmethod
    def save_excel_file(file_obj, name, description=None):
        """

        """
        try:
            excel_file = ExcelFile.objects.create(
                name=name,
                description=description,
                file=file_obj
            )
            return excel_file
        except Exception as e:
            logger.error(f"Error al guardar archivo Excel: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    @staticmethod
    def read_excel_sheets(excel_file_id):
        """

        """
        try:
            excel_file = ExcelFile.objects.get(id=excel_file_id)

            # Usamos pandas para leer el Excel
            xls = pd.ExcelFile(excel_file.file.path)
            sheet_names = xls.sheet_names

            sheets = []
            for sheet_name in sheet_names:
                # Contar filas para cada hoja
                df = pd.read_excel(excel_file.file.path, sheet_name=sheet_name)
                row_count = len(df)

                # Crear o actualizar el registro de la hoja
                sheet, created = ExcelSheet.objects.update_or_create(
                    excel_file=excel_file,
                    name=sheet_name,
                    defaults={'row_count': row_count}
                )
                sheets.append(sheet)

            return sheets
        except Exception as e:
            excel_file.error = str(e)
            excel_file.save()
            logger.error(f"Error al leer hojas de Excel: {str(e)}")
            raise
