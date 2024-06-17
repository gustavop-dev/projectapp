from django.db import models

class Designs(models.Model):
    title_en = models.CharField(max_length=255, verbose_name="Title (English)")
    title_es = models.CharField(max_length=255, verbose_name="Title (Spanish)")
    presentation_image = models.ImageField(upload_to='designs/presentation/')
    detail_image = models.ImageField(upload_to='designs/detail/')

    def __str__(self):
        return self.title_en