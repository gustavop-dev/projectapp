import random
from faker import Faker
from django.core.management.base import BaseCommand
from content.models import Product, Category, Item

class Command(BaseCommand):
    help = 'Create fake Product, Category, and Item records in the database'

    def add_arguments(self, parser):
        parser.add_argument('number_of_products', type=int, nargs='?', default=10)

    def handle(self, *args, **options):
        number_of_products = options['number_of_products']
        fake = Faker()

        # List of test images for products
        test_images = [
            'media/temp/products/image_temp1.jpg',
            'media/temp/products/image_temp2.jpg',
            'media/temp/products/image_temp3.jpg',
            'media/temp/products/image_temp4.jpg',
        ]

        # Create fake items
        items = []
        for i in range(1, 11):
            item = Item.objects.create(
                name_en=f'Item {i} EN',
                name_es=f'Item {i} ES'
            )
            items.append(item)
            self.stdout.write(self.style.SUCCESS(f'Item "{item.name_en}" created'))

        # Create fake categories and associate items
        categories = []
        for i in range(1, 6):
            category = Category.objects.create(
                name_en=f'Category {i} EN',
                name_es=f'Category {i} ES'
            )
            category.items.add(*random.sample(items, k=random.randint(1, len(items))))
            categories.append(category)
            self.stdout.write(self.style.SUCCESS(f'Category "{category.name_en}" created'))

        # Create fake products and associate categories
        for i in range(1, number_of_products + 1):
            title_en = f'Product {i} EN'
            title_es = f'Product {i} ES'
            description_en = fake.text(max_nb_chars=500) + ' (EN)'
            description_es = fake.text(max_nb_chars=500) + ' (ES)'
            development_time_en = f'{random.randint(1, 6)} weeks (EN)'
            development_time_es = f'{random.randint(1, 6)} semanas (ES)'
            price = random.uniform(100, 1000)

            product = Product.objects.create(
                title_en=title_en,
                title_es=title_es,
                description_en=description_en,
                description_es=description_es,
                price=round(price, 2),
                development_time_en=development_time_en,
                development_time_es=development_time_es,
                image=random.choice(test_images)
            )
            product.categories.add(*random.sample(categories, k=random.randint(1, len(categories))))

            self.stdout.write(self.style.SUCCESS(f'Product "{product.title_en}" created'))

        self.stdout.write(self.style.SUCCESS(f'{number_of_products} Product records created'))
