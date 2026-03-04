from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class BlogPost(models.Model):
    """
    Model for blog articles.

    Each post has a title, slug (auto-generated), cover image,
    excerpt for cards/listing, full HTML content, and a JSON list
    of sources consulted (each with name and url).
    """

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    cover_image = models.ImageField(upload_to='blog/covers/', blank=True)
    excerpt = models.TextField(
        help_text='Short summary shown on listing cards (1-2 sentences).'
    )
    content = models.TextField(
        help_text='Full article content in HTML.'
    )
    sources = models.JSONField(
        default=list, blank=True,
        help_text='List of {name, url} objects for consulted sources.'
    )
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at', '-created_at']
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
