from django.db import models
from django.contrib.auth.models import User

from groups.models import Group
from users.models import Role


class LearningStage(models.Model):
    """
    ORM модель этапа обучения
    """

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="stages")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    sequence_number = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.sequence_number}. {self.title}"


class Enrollment(models.Model):
    """
    ORM модель для записи на учебную программу
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="enrollments")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="enrollments")

    def __str__(self):
        return f"{self.user.username} → {self.group.name} ({self.role.role})"