from django.db import models

class Contact(models.Model):
    """
    Contact model representing a message sent by a user through the contact form.

    Attributes:
        email (EmailField): The email address of the user who sent the message.
        subject (CharField): The subject of the message.
        message (TextField): The body of the message.
    """
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()

    def __str__(self):
        return self.subject
