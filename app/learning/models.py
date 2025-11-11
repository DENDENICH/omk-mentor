from django.db import models

from groups.models import Group
from users.models import AuthUser

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

    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE, related_name="enrollments")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="enrollments")
    role = models.CharField(
        max_length=20, 
        choices=(
            ("student", "Студент"),
            ("mentor", "Ментор")
        ), 
        verbose_name="Роль"
    )


    def __str__(self):
        return f"{self.user.username} → {self.group.name} ({self.role})"