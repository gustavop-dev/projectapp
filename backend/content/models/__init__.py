"""
This package initializes the models for the ProjectApp application.

The following models are imported:
    - Contact: Model handling contact-related information.
    - Design: Model representing various design-related entries.
    - Model3D: Model for 3D objects and representations.
    - Product, Category, Item: Models related to product offerings.
    - Hosting: Model for hosting services.
    - PortfolioWork: Model for portfolio work entries.
"""

from .contact import Contact
from .design import Design
from .model_3d import Model3D
from .product import Item, Category, Product
from .hosting import Hosting
from .portfolio_works import PortfolioWork
