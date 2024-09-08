from django.db import models

class Models3D(models.Model):
    """
    Models3D model representing 3D models in the ProjectApp.

    Attributes:
        title_en (str): The title of the 3D model in English.
        title_es (str): The title of the 3D model in Spanish.
        image (ImageField): An image representing the 3D model.
        file (FileField): The file containing the 3D model data.
    """
    title_en = models.CharField(max_length=255, verbose_name="Title (English)")
    title_es = models.CharField(max_length=255, verbose_name="Title (Spanish)")
    image = models.ImageField(upload_to='3dmodels/images/')
    file = models.FileField(upload_to='3dmodels/files/')

    def __str__(self):
        return self.title_en
