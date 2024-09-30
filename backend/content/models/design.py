import os
from django.db import models

class Design(models.Model):
    """
    Design model representing design entries in the ProjectApp.

    Attributes:
        title_en (str): The title of the design in English.
        title_es (str): The title of the design in Spanish.
        cover_image (ImageField): The image used for the cover presentation of the design.
        detail_image (ImageField): The image used for showing the details of the design.
        category_title_en (str): The title of the category in English.
        category_title_es (str): The title of the category in Spanish.
    """
    title_en = models.CharField(max_length=255, verbose_name="Title (English)")
    title_es = models.CharField(max_length=255, verbose_name="Title (Spanish)")
    cover_image = models.ImageField(upload_to='designs/cover/')
    detail_image = models.ImageField(upload_to='designs/detail/')
    category_title_en = models.CharField(max_length=255, verbose_name="Category Title (English)")
    category_title_es = models.CharField(max_length=255, verbose_name="Category Title (Spanish)")

    def __str__(self):
        return self.title_en
    
    def delete(self, *args, **kwargs):
        # Remove cover and detail images before deleting the record
        if self.cover_image and os.path.isfile(self.cover_image.path):
            os.remove(self.cover_image.path)
        if self.detail_image and os.path.isfile(self.detail_image.path):
            os.remove(self.detail_image.path)
        super().delete(*args, **kwargs)
