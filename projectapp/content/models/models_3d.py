from django.db import models

class Models3D(models.Model):
    title_en = models.CharField(max_length=255, verbose_name="Title (English)")
    title_es = models.CharField(max_length=255, verbose_name="Title (Spanish)")
    image = models.ImageField(upload_to='3dmodels/images/')
    file = models.FileField(upload_to='3dmodels/files/')

    def __str__(self):
        return self.title_en