from django.db import models

from users.models import AuthUser


class Group(models.Model):
    """
    ORM модель групп
    """

    name = models.CharField(max_length=255)
    organizer = models.ForeignKey(AuthUser, on_delete=models.CASCADE, related_name="organized_groups")

    def __str__(self):
        return self.name
