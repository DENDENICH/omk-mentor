from django.db import transaction
from rest_framework import serializers
import pandas as pd
from io import BytesIO

from .models import Group, Subgroup
from learning.models import Enrollment
from users.models import AuthUser, Profile


class GroupExcelUploadSerializer(serializers.Serializer):
    file = serializers.FileField()


class GroupTemplateDownloadSerializer(serializers.Serializer):
    # может быть пустым, просто GET для шаблона
    pass


class EnrollmentRowSerializer(serializers.Serializer):
    tab_number = serializers.CharField()
    role = serializers.ChoiceField(choices=[("student","student"), ("mentor","mentor")])


class GroupTemplateSerializer(serializers.Serializer):

    def build_template(self):
        group_name = "your_group_name"
        # Примеры: организатор, ментор, студент (студент привязан к ментору)
        data = [
            {"Табельный номер": "1111", "Роль": "Организатор", "Табельный номер наставника": ""},
            {"Табельный номер": "2222", "Роль": "Наставник", "Табельный номер наставника": ""},
            {"Табельный номер": "3333", "Роль": "Студент", "Табельный номер наставника": "2222"},
        ]
        df = pd.DataFrame(data, columns=["Табельный номер", "Роль", "Табельный номер наставника"])
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="GroupImport")
        buffer.seek(0)
        filename = f"{group_name}.xlsx"
        return buffer, filename

class GroupUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    group_name = serializers.CharField()

    roles = {
        "Организатор": "organizer",
        "Ментор": "mentor",
        "Студент": "student"
    }

    def validate_file(self, value):
        try:
            df = pd.read_excel(value, engine="openpyxl")
        except Exception as e:
            raise serializers.ValidationError(f"Ошибка при чтении Excel: {e}")
        expected = {"Табельный номер", "Роль", "Табельный номер наставника"}
        if not expected.issubset(df.columns):
            missing = expected - set(df.columns)
            raise serializers.ValidationError(f"Отсутствуют колонки: {missing}")
        self._df = df
        return value

    def save(self, **kwargs):
        result = {"created_subgroups": [], "enrollments": [], "errors": []}

        group_name = self.validated_data["group_name"]
        df = self._df

        with transaction.atomic():
            # Получаем или создаём группу
            group, group_created = Group.objects.get_or_create(name=group_name)

            # Проходим по строкам
            for idx, row in df.iterrows():
                tab = str(row["Табельный номер"]).strip()
                role = self.roles.get(row["Роль"])
                if role is None:
                    raise serializers.ValidationError(f"Неверное значение роли у пользователя - '{tab}'")
                mentor_tab = str(row["Табельный номер наставника"]).strip() if pd.notna(row["mentor_tab_number"]) else ""

                # Найти пользователя
                try:
                    user = AuthUser.objects.get(tab_number=tab)
                except AuthUser.DoesNotExist:
                    result["errors"].append({"row": idx + 2, "detail": f"Пользователь с таб. номером {tab} не найден"})
                    continue

                profile = user.profile
                account_role = profile.account_role  # “admin”, “organizer” или None

                # Правила:
                if account_role == "organizer" and role in ("mentor", "student"):
                    result["errors"].append({"row": idx + 2, "detail": "Организатор не может быть ментором или студентом"})
                    continue
                if account_role == "admin":
                    result["errors"].append({"row": idx + 2, "detail": "Администратор не может быть участником группы"})
                    continue

                # Если роль — mentor или student, работаем с подгруппой
                subgroup = None
                if role == "student":
                    if not mentor_tab:
                        result["errors"].append({"row": idx + 2, "detail": "Не указан табельный номер наставника (mentor_tab_number)"})
                        continue

                    # Найти менторского пользователя
                    try:
                        mentor = AuthUser.objects.get(tab_number=mentor_tab)
                    except AuthUser.DoesNotExist:
                        result["errors"].append({"row": idx + 2, "detail": f"Ментор с таб. номером {mentor_tab} не найден"})
                        continue

                    # Найти или создать подгруппу, привязанную к этой группе + ментору
                    subgroup, sub_created = Subgroup.objects.get_or_create(
                        group=group,
                        name=f"{group.name}-{mentor.first_name + ' ' + mentor.last_name}"  # можно название подгруппы составить из группы + mentor
                    )
                    if sub_created:
                        result["created_subgroups"].append({"mentor_tab": mentor.tab_number, "subgroup_id": subgroup.id})

                # Создаём или обновляем Enrollment
                enrollment, en_created = Enrollment.objects.get_or_create(
                    user=user,
                    subgroup=subgroup,
                    defaults={"role": role, "is_active": True}
                )
                if not en_created:
                    enrollment.role = role
                    enrollment.is_active = True
                    enrollment.save()

                result["enrollments"].append({
                    "tab_number": tab,
                    "role": role,
                    "mentor_tab_number": mentor_tab,
                    "subgroup_id": subgroup.id if subgroup else None,
                    "created": en_created
                })

            return result