import os
from django.db import models

class Hosting(models.Model):
    """
    Hosting model representing hosting plans for the software house.

    Attributes:
        title_en (str): The title of the hosting plan in English.
        title_es (str): The title of the hosting plan in Spanish.
        description_en (str): A brief description of the plan in English.
        description_es (str): A brief description of the plan in Spanish.
        monthly_price (Decimal): The monthly price of the hosting plan.
        annual_price (Decimal): The annual price of the hosting plan.
        cpu_cores_en (str): Number of CPU cores (in English).
        cpu_cores_es (str): Number of CPU cores (in Spanish).
        ram_en (str): RAM size (in English).
        ram_es (str): RAM size (in Spanish).
        storage_en (str): Storage space (in English).
        storage_es (str): Storage space (in Spanish).
        bandwidth_en (str): Bandwidth allowance (in English).
        bandwidth_es (str): Bandwidth allowance (in Spanish).
        data_center_location_en (str): Data center location (in English).
        data_center_location_es (str): Data center location (in Spanish).
        operating_system_en (str): Operating system (in English).
        operating_system_es (str): Operating system (in Spanish).
    """
    title_en = models.CharField(max_length=255, verbose_name="Title (English)")
    title_es = models.CharField(max_length=255, verbose_name="Title (Spanish)")
    description_en = models.CharField(max_length=255, verbose_name="Description (English)")
    description_es = models.CharField(max_length=255, verbose_name="Description (Spanish)")
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monthly Price")
    annual_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Annual Price")
    cpu_cores_en = models.CharField(max_length=255, verbose_name="CPU Cores (English)")
    cpu_cores_es = models.CharField(max_length=255, verbose_name="CPU Cores (Spanish)")
    ram_en = models.CharField(max_length=255, verbose_name="RAM (English)")
    ram_es = models.CharField(max_length=255, verbose_name="RAM (Spanish)")
    storage_en = models.CharField(max_length=255, verbose_name="Storage (English)")
    storage_es = models.CharField(max_length=255, verbose_name="Storage (Spanish)")
    bandwidth_en = models.CharField(max_length=255, verbose_name="Bandwidth (English)")
    bandwidth_es = models.CharField(max_length=255, verbose_name="Bandwidth (Spanish)")
    data_center_location_en = models.CharField(max_length=255, verbose_name="Data Center Location (English)")
    data_center_location_es = models.CharField(max_length=255, verbose_name="Data Center Location (Spanish)")
    operating_system_en = models.CharField(max_length=255, verbose_name="Operating System (English)")
    operating_system_es = models.CharField(max_length=255, verbose_name="Operating System (Spanish)")

    def __str__(self):
        return self.title_en
