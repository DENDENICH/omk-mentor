from django.db import models
from django.contrib.auth.models import User


class Group(models.Model):
    """
    ORM модель групп
    """

    name = models.CharField(max_length=255)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_groups")

    def __str__(self):
        return self.name
