from django.db import models

from learning.models import Enrollment, LearningStage


class Progress(models.Model):
    """
    ORM модель для прогресса
    """

    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="progress")
    stage = models.ForeignKey(LearningStage, on_delete=models.CASCADE, related_name="progress")
    status_progress = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.enrollment.user.username} - {self.stage.title}: {self.status_progress}"
