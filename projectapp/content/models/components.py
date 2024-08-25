from django.db import models


class Example(models.Model):
    """
    Example model representing an example associated with components.

    Attributes:
        title_en (str): The title of the example in English.
        title_es (str): The title of the example in Spanish.
        image (ImageField): An image representing the example.
    """
    title_en = models.CharField(max_length=255, verbose_name="Title (English)")
    title_es = models.CharField(max_length=255, verbose_name="Title (Spanish)")
    image = models.ImageField(upload_to='components/examples/')

    def __str__(self):
        return self.title_en


class Components(models.Model):
    """
    Components model representing individual components of a project.

    Attributes:
        title_en (str): The title of the component in English.
        title_es (str): The title of the component in Spanish.
        image (ImageField): An image representing the component.
        examples (ManyToManyField): A relation to multiple examples associated with the component.
    """
    title_en = models.CharField(max_length=255, verbose_name="Title (English)")
    title_es = models.CharField(max_length=255, verbose_name="Title (Spanish)")
    image = models.ImageField(upload_to='components/images/')
    examples = models.ManyToManyField(Example, related_name='components')

    def __str__(self):
        return self.title_en


class Section(models.Model):
    """
    Section model representing a section of a project which contains multiple components.

    Attributes:
        title_en (str): The title of the section in English.
        title_es (str): The title of the section in Spanish.
        components (ManyToManyField): A relation to multiple components within this section.
    """
    title_en = models.CharField(max_length=255, verbose_name="Title (English)")
    title_es = models.CharField(max_length=255, verbose_name="Title (Spanish)")
    components = models.ManyToManyField(Components, related_name='sections')

    def __str__(self):
        return self.title_en


class CategoriesDevelopment(models.Model):
    """
    CategoriesDevelopment model representing a development category which contains multiple sections.

    Attributes:
        title_en (str): The title of the category in English.
        title_es (str): The title of the category in Spanish.
        description_en (TextField): The description of the category in English.
        description_es (TextField): The description of the category in Spanish.
        sections (ManyToManyField): A relation to multiple sections under this category.
    """
    title_en = models.CharField(max_length=255, verbose_name="Title (English)")
    title_es = models.CharField(max_length=255, verbose_name="Title (Spanish)")
    description_en = models.TextField(verbose_name="Description (English)")
    description_es = models.TextField(verbose_name="Description (Spanish)")
    sections = models.ManyToManyField(Section, related_name='categories')

    def __str__(self):
        return self.title_en
