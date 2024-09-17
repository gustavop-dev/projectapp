"""
This package initializes the models for the ProjectApp application.

The following models are imported:
    - Contact: Model handling contact-related information.
    - Design: Model representing various design-related entries.
    - Model3D: Model for 3D objects and representations.
    - Example: Model used for storing examples related to components.
    - Component: Model representing individual components in the project.
    - Section: Model for defining sections of the development process.
    - UISectionCategory: Model handling development categories.
"""

from .contact import Contact
from .design import Design
from .model_3d import Model3D
from .product import Item, Category, Product
from .component import Example, Component, Section, UISectionCategory
