from django.db import models

class Contact(models.Model):
    """
    Contact model representing a message sent by a user through the contact form.

    Attributes:
        email (EmailField): The email address of the user who sent the message.
        phone_number (CharField): The phone number of the user (optional).
        subject (CharField): The subject of the message.
        message (TextField): The body of the message.
        budget (CharField): The budget range selected by the user (optional).
    """
    BUDGET_CHOICES = [
        ('500-5K', '500-5K'),
        ('5-10K', '5-10K'),
        ('10-20K', '10-20K'),
        ('20-30K', '20-30K'),
        ('>30K', '>30K'),
    ]
    
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    subject = models.CharField(max_length=255)
    message = models.TextField(blank=True, null=True)
    budget = models.CharField(max_length=10, choices=BUDGET_CHOICES, blank=True, null=True)

    def __str__(self):
        return self.subject
