from django.db import models


class Example(models.Model):
    title_en = models.CharField(max_length=255, verbose_name="Title (English)")
    title_es = models.CharField(max_length=255, verbose_name="Title (Spanish)")
    image = models.ImageField(upload_to='components/examples/')

    def __str__(self):
        return self.title_en


class Components(models.Model):
    title_en = models.CharField(max_length=255, verbose_name="Title (English)")
    title_es = models.CharField(max_length=255, verbose_name="Title (Spanish)")
    image = models.ImageField(upload_to='components/images/')
    examples = models.ManyToManyField(Example, related_name='components')

    def __str__(self):
        return self.title_en


class Section(models.Model):
    title_en = models.CharField(max_length=255, verbose_name="Title (English)")
    title_es = models.CharField(max_length=255, verbose_name="Title (Spanish)")
    components = models.ManyToManyField(Components, related_name='sections')

    def __str__(self):
        return self.title_en


class CategoriesDevelopment(models.Model):
    title_en = models.CharField(max_length=255, verbose_name="Title (English)")
    title_es = models.CharField(max_length=255, verbose_name="Title (Spanish)")
    description_en = models.TextField(verbose_name="Description (English)")
    description_es = models.TextField(verbose_name="Description (Spanish)")
    sections = models.ManyToManyField(Section, related_name='categories')

    def __str__(self):
        return self.title_en