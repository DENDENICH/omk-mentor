from django.db import models
from django.contrib.auth.models import User

from django.core.validators import RegexValidator


class Profile(models.Model):
    """
    ORM модель для пользователей
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tab_number = models.CharField(
        max_length=255,
        unique=True,
        validators=[RegexValidator(r'^\w+$', 'Табельный номер может содержать только буквы/цифры/нижнее подчеркивание')]
    )

    def __repr__(self):
        return f"{self.user.username} ({self.user.email})"


