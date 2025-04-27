from django.db import models
from excel_files.models import ExcelSheet


class DataTable(models.Model):
    """Modelo para almacenar tablas de datos generadas a partir de Excel"""
    sheet = models.OneToOneField(ExcelSheet, on_delete=models.CASCADE, related_name='data_table')
    table_name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    row_count = models.IntegerField(default=0)

    objects = models.Manager()

    def __str__(self):
        return self.table_name


class DataRow(models.Model):
    """Modelo para almacenar filas de datos genéricas"""
    table = models.ForeignKey(DataTable, on_delete=models.CASCADE, related_name='rows')
    row_index = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        unique_together = ('table', 'row_index')

    def __str__(self):
        return f"{self.table.table_name} - Row {self.row_index}"


class DataCell(models.Model):
    """Modelo para almacenar celdas de datos de manera genérica"""
    row = models.ForeignKey(DataRow, on_delete=models.CASCADE, related_name='cells')
    column_definition = models.ForeignKey('excel_files.ColumnDefinition', on_delete=models.CASCADE)

    # Campos para almacenar diferentes tipos de datos
    string_value = models.TextField(blank=True, null=True)
    integer_value = models.IntegerField(blank=True, null=True)
    float_value = models.FloatField(blank=True, null=True)
    date_value = models.DateField(blank=True, null=True)
    datetime_value = models.DateTimeField(blank=True, null=True)
    boolean_value = models.BooleanField(blank=True, null=True)

    objects = models.Manager()

    def __str__(self):
        return f"{self.row} - {self.column_definition.name}"

    def get_value(self):
        """Devuelve el valor según el tipo de datos de la columna"""
        data_type = self.column_definition.data_type
        if data_type == 'string':
            return self.string_value
        elif data_type == 'integer':
            return self.integer_value
        elif data_type == 'float':
            return self.float_value
        elif data_type == 'date':
            return self.date_value
        elif data_type == 'datetime':
            return self.datetime_value
        elif data_type == 'boolean':
            return self.boolean_value
        return None


class TableExport(models.Model):
    """Modelo para almacenar información sobre exportaciones de tablas"""
    FORMAT_CHOICES = (
        ('parquet', 'Parquet'),
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
    )

    table = models.ForeignKey(DataTable, on_delete=models.CASCADE, related_name='exports')
    file = models.FileField(upload_to='exports/')
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    file_size = models.BigIntegerField(default=0)  # Tamaño en bytes

    objects = models.Manager()

    def __str__(self):
        return f"{self.table.table_name} - {self.format} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

    def get_file_size_display(self):
        """Devuelve el tamaño del archivo en formato legible"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024 or unit == 'GB':
                return f"{size:.2f} {unit}"
            size /= 1024
