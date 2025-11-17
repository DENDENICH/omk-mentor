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

class Subgroup(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="subgroups")
    name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.group.name} — {self.name or self.mentor.tab_number}"