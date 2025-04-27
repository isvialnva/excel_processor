from django.db import models
import uuid
import os


def get_file_path(instance, filename):
    """Genera una ruta única para cada archivo subido"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('excel_files', filename)


class ExcelFile(models.Model):
    """

    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to=get_file_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    error = models.TextField(blank=True, null=True)

    objects = models.Manager()

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        """

        """
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super(ExcelFile, self).delete(*args, **kwargs)


class ExcelSheet(models.Model):
    """

    """
    excel_file = models.ForeignKey(ExcelFile, on_delete=models.CASCADE, related_name='sheets')
    name = models.CharField(max_length=255)
    row_count = models.IntegerField(default=0)
    processed = models.BooleanField(default=False)

    objects = models.Manager()

    class Meta:
        unique_together = ('excel_file', 'name')

    def __str__(self):
        return f"{self.excel_file.name} - {self.name}"


class ColumnDefinition(models.Model):
    """

    """
    DATA_TYPES = (
        ('string', 'Texto'),
        ('integer', 'Entero'),
        ('float', 'Decimal'),
        ('date', 'Fecha'),
        ('datetime', 'Fecha y Hora'),
        ('boolean', 'Booleano'),
        ('unknown', 'Desconocido'),
    )

    sheet = models.ForeignKey(ExcelSheet, on_delete=models.CASCADE, related_name='columns')
    name = models.CharField(max_length=255)
    original_name = models.CharField(max_length=255)
    column_index = models.IntegerField()
    data_type = models.CharField(max_length=20, choices=DATA_TYPES)
    nullable = models.BooleanField(default=True)

    objects = models.Manager()

    class Meta:
        unique_together = ('sheet', 'column_index')

    def __str__(self):
        return f"{self.sheet.name} - {self.name} ({self.data_type})"
