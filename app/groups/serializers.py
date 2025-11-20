from django.db import transaction
from rest_framework import serializers
import pandas as pd
from io import BytesIO

from .models import Group, Subgroup
from learning.models import Enrollment
from users.models import AuthUser, Profile

# from .bussines_logic.creating_group.creating_group import GroupDataFrame
from .exceptions import FileException



class GroupTemplateDownloadSerializer(serializers.Serializer):
    # может быть пустым, просто GET для шаблона
    pass


class EnrollmentSerializer(serializers.Serializer):
    """
    Membership JSON object
    """
    tab = serializers.CharField()
    role = serializers.ChoiceField(["mentor", "student", "organizer", ], default="")
    mentor_tab = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class GroupImportSchemaSerializer(serializers.Serializer):
    """
    Group's data JSON object
    """
    group_name = serializers.CharField()
    organizer = EnrollmentSerializer()
    members = EnrollmentSerializer(many=True)

    def validate(self, attrs) -> dict:
        members = attrs.get("members")

        for member in members:
            if member["role"] == "student" and not member.get("mentor_tab"):
                raise serializers.ValidationError(
                    f"Студент {member.get('tab')} должен иметь mentor_tab"
                )

        return attrs

