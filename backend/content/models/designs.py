from django.db import models

class Designs(models.Model):
    """
    Designs model representing design entries in the ProjectApp.

    Attributes:
        title_en (str): The title of the design in English.
        title_es (str): The title of the design in Spanish.
        presentation_image (ImageField): The image used for the presentation of the design.
        detail_image (ImageField): The image used for showing the details of the design.
    """
    title_en = models.CharField(max_length=255, verbose_name="Title (English)")
    title_es = models.CharField(max_length=255, verbose_name="Title (Spanish)")
    presentation_image = models.ImageField(upload_to='designs/presentation/')
    detail_image = models.ImageField(upload_to='designs/detail/')

    def __str__(self):
        return self.title_en
