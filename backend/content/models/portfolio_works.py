import os
from django.db import models

class PortfolioWork(models.Model):
    """
    PortfolioWork model representing completed projects or works in the ProjectApp.

    Attributes:
        title_en (str): The title of the work in English.
        title_es (str): The title of the work in Spanish.
        cover_image (ImageField): The image used for the cover presentation of the work.
        project_url (URLField): The URL that redirects to the live project or case study.
        category_title_en (str): The category of the work in English.
        category_title_es (str): The category of the work in Spanish.
    """
    title_en = models.CharField(max_length=255, verbose_name="Title (English)")
    title_es = models.CharField(max_length=255, verbose_name="Title (Spanish)")
    cover_image = models.ImageField(upload_to='portfolio/cover/')
    project_url = models.URLField(verbose_name="Project URL", max_length=500)
    category_title_en = models.CharField(max_length=255, verbose_name="Category Title (English)")
    category_title_es = models.CharField(max_length=255, verbose_name="Category Title (Spanish)")

    def __str__(self):
        return self.title_en
    
    def delete(self, *args, **kwargs):
        # Remove cover image before deleting the record
        if self.cover_image and os.path.isfile(self.cover_image.path):
            os.remove(self.cover_image.path)
        super().delete(*args, **kwargs)