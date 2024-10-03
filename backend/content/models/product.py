import os
from django.db import models

class Item(models.Model):
    """
    Item model representing individual items used in products.

    Attributes:
        name_en (str): The name of the item in English.
        name_es (str): The name of the item in Spanish.
    """
    name_en = models.CharField(max_length=255, verbose_name="Item Name (English)")
    name_es = models.CharField(max_length=255, verbose_name="Item Name (Spanish)")

    def __str__(self):
        return self.name_en


class Category(models.Model):
    """
    Category model representing a category of products.

    Attributes:
        name_en (str): The name of the category in English.
        name_es (str): The name of the category in Spanish.
        items (ManyToManyField): A relation to multiple items associated with the category.
    """
    name_en = models.CharField(max_length=255, verbose_name="Category Name (English)")
    name_es = models.CharField(max_length=255, verbose_name="Category Name (Spanish)")
    items = models.ManyToManyField(Item, related_name='categories')

    def __str__(self):
        return self.name_en


class Product(models.Model):
    """
    Product model representing products with details in English and Spanish.

    Attributes:
        title_en (str): The title of the product in English.
        title_es (str): The title of the product in Spanish.
        description_en (TextField): The description of the product in English.
        description_es (TextField): The description of the product in Spanish.
        price (DecimalField): The price of the product.
        development_time_en (str): The development time of the product in English.
        development_time_es (str): The development time of the product in Spanish.
        categories (ManyToManyField): A relation to multiple categories associated with the product.
        image (ImageField): An image representing the product.
    """
    title_en = models.CharField(max_length=255, verbose_name="Title (English)")
    title_es = models.CharField(max_length=255, verbose_name="Title (Spanish)")
    description_en = models.TextField(verbose_name="Description (English)")
    description_es = models.TextField(verbose_name="Description (Spanish)")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price")
    development_time_en = models.CharField(max_length=255, verbose_name="Development Time (English)")
    development_time_es = models.CharField(max_length=255, verbose_name="Development Time (Spanish)")
    categories = models.ManyToManyField(Category, related_name='products')
    image = models.ImageField(upload_to='products/images/')

    def __str__(self):
        return self.title_en

    def delete(self, *args, **kwargs):
        # Remove image file before deleting the record
        if self.image and os.path.isfile(self.image.path):
            os.remove(self.image.path)
        super().delete(*args, **kwargs)