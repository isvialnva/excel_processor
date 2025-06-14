# Generated by Django 5.2 on 2025-04-27 18:08

import django.db.models.deletion
import excel_files.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ExcelFile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, null=True)),
                ("file", models.FileField(upload_to=excel_files.models.get_file_path)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("processed", models.BooleanField(default=False)),
                ("error", models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="ExcelSheet",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("row_count", models.IntegerField(default=0)),
                ("processed", models.BooleanField(default=False)),
                (
                    "excel_file",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sheets",
                        to="excel_files.excelfile",
                    ),
                ),
            ],
            options={
                "unique_together": {("excel_file", "name")},
            },
        ),
        migrations.CreateModel(
            name="ColumnDefinition",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("original_name", models.CharField(max_length=255)),
                ("column_index", models.IntegerField()),
                (
                    "data_type",
                    models.CharField(
                        choices=[
                            ("string", "Texto"),
                            ("integer", "Entero"),
                            ("float", "Decimal"),
                            ("date", "Fecha"),
                            ("datetime", "Fecha y Hora"),
                            ("boolean", "Booleano"),
                            ("unknown", "Desconocido"),
                        ],
                        max_length=20,
                    ),
                ),
                ("nullable", models.BooleanField(default=True)),
                (
                    "sheet",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="columns",
                        to="excel_files.excelsheet",
                    ),
                ),
            ],
            options={
                "unique_together": {("sheet", "column_index")},
            },
        ),
    ]
