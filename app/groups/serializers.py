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

    roles = {
        "Организатор": "organizer",
        "Наставник": "mentor",
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
        self._file_name = value.name
        return value

    # def save(self, **kwargs):
    #     result = {"created_subgroups": [], "enrollments": [], "errors": []}
    #
    #     group_name = self._file_name
    #     df = self._df
    #
    #     with transaction.atomic():
    #         # Получаем или создаём группу
    #         group, group_created = Group.objects.get_or_create(name=group_name)0
    #
    #         # Проходим по строкам
    #         for idx, row in df.iterrows():
    #             tab = str(row["Табельный номер"]).strip()
    #             role = self.roles.get(row["Роль"])
    #             if role is None:
    #                 raise serializers.ValidationError(f"Неверное значение роли у пользователя - '{tab}'")
    #             mentor_tab = str(row["Табельный номер наставника"]).strip() if pd.notna(row["mentor_tab_number"]) else ""
    #
    #             # Найти пользователя
    #             try:
    #                 user = AuthUser.objects.get(tab_number=tab)
    #             except AuthUser.DoesNotExist:
    #                 result["errors"].append({"row": idx + 2, "detail": f"Пользователь с таб. номером {tab} не найден"})
    #                 continue
    #
    #             profile = user.profile
    #             account_role = profile.account_role  # “admin”, “organizer” или None
    #
    #             # Правила:
    #             if account_role == "organizer" and role in ("mentor", "student"):
    #                 result["errors"].append({"row": idx + 2, "detail": "Организатор не может быть ментором или студентом"})
    #                 continue
    #             if account_role == "admin":
    #                 result["errors"].append({"row": idx + 2, "detail": "Администратор не может быть участником группы"})
    #                 continue
    #
    #             # Если роль — mentor или student, работаем с подгруппой
    #             subgroup = None
    #             if role == "student":
    #                 if not mentor_tab:
    #                     result["errors"].append({"row": idx + 2, "detail": "Не указан табельный номер наставника (mentor_tab_number)"})
    #                     continue
    #
    #                 # Найти менторского пользователя
    #                 try:
    #                     mentor = AuthUser.objects.get(tab_number=mentor_tab)
    #                 except AuthUser.DoesNotExist:
    #                     result["errors"].append({"row": idx + 2, "detail": f"Ментор с таб. номером {mentor_tab} не найден"})
    #                     continue
    #
    #                 # Найти или создать подгруппу, привязанную к этой группе + ментору
    #                 subgroup, sub_created = Subgroup.objects.get_or_create(
    #                     group=group,
    #                     name=f"{group.name}-{mentor.first_name + ' ' + mentor.last_name}"  # можно название подгруппы составить из группы + mentor
    #                 )
    #                 if sub_created:
    #                     result["created_subgroups"].append({"mentor_tab": mentor.tab_number, "subgroup_id": subgroup.id})
    #
    #             # Создаём или обновляем Enrollment
    #             enrollment, en_created = Enrollment.objects.get_or_create(
    #                 user=user,
    #                 subgroup=subgroup,
    #                 defaults={"role": role, "is_active": True}
    #             )
    #             if not en_created:
    #                 enrollment.role = role
    #                 enrollment.is_active = True
    #                 enrollment.save()
    #
    #             result["enrollments"].append({
    #                 "tab_number": tab,
    #                 "role": role,
    #                 "mentor_tab_number": mentor_tab,
    #                 "subgroup_id": subgroup.id if subgroup else None,
    #                 "created": en_created
    #             })
    #
    #         return result

    def save(self, **kwargs):
        df = self._df
        result = {"created_subgroups": [], "enrollments": [], "errors": []}
        group_name = self._file_name

        # -----------------------------------
        # 1. Первый проход — сбор данных
        # -----------------------------------
        users_cache = {}
        mentors_cache = {}
        enrollment_plan = []
        subgroup_plan = {}

        organizer_user = None
        organizer_rows = []

        for idx, row in df.iterrows():
            row_num = idx + 2

            tab = str(row["Табельный номер"]).strip()
            role_str = row["Роль"]
            role = self.roles.get(role_str)

            if role is None:
                result["errors"].append({"row": row_num, "detail": f"Неверная роль '{role_str}' у {tab}"})
                continue

            # ----------- Найти пользователя ----------
            try:
                user = AuthUser.objects.get(tab_number=tab)
            except AuthUser.DoesNotExist:
                result["errors"].append({"row": row_num, "detail": f"Пользователь {tab} не найден"})
                continue

            users_cache[tab] = user
            profile = user.profile
            account_role = profile.account_role

            # ----------- ROLE: ORGANIZER ------------
            if role == "organizer":
                organizer_rows.append(row_num)

                if organizer_user is None:
                    organizer_user = user
                continue  # организатор НЕ участвует в подгруппах

            # ----------- Проверка корректности роли ----------
            if account_role == "admin":
                result["errors"].append({"row": row_num, "detail": "Администратор не может участвовать в группе"})
                continue

            if account_role == "organizer" and role in ("mentor", "student"):
                result["errors"].append({"row": row_num, "detail": "Организатор не может быть ментором/студентом"})
                continue

            # ----------- ROLE: STUDENT -------------
            mentor_tab = None
            if role == "student":
                mentor_tab = (
                    str(row["Табельный номер наставника"]).strip()
                    if pd.notna(row["Табельный номер наставника"])
                    else ""
                )
                if not mentor_tab:
                    result["errors"].append({"row": row_num, "detail": "Не указан наставник для студента"})
                    continue

                try:
                    mentor = AuthUser.objects.get(tab_number=mentor_tab)
                except AuthUser.DoesNotExist:
                    result["errors"].append({"row": row_num, "detail": f"Наставник {mentor_tab} не найден"})
                    continue

                mentors_cache[mentor_tab] = mentor

                # Планируем создание подгруппы
                if mentor_tab not in subgroup_plan:
                    subgroup_plan[mentor_tab] = {
                        "mentor": mentor,
                        "name": f"{group_name}-{mentor.first_name} {mentor.last_name}"
                    }

            # ----------- Собираем план Enrollment ----------
            enrollment_plan.append({
                "user": user,
                "role": role,
                "mentor_tab": mentor_tab,
                "subgroup_key": mentor_tab,  # None для mentor
                "excel_row": row_num
            })

        # -----------------------------------
        # 2. Проверки
        # -----------------------------------
        if organizer_user is None:
            raise serializers.ValidationError("В файле не указан организатор (роль 'Организатор')")

        if len(organizer_rows) > 1:
            raise serializers.ValidationError(f"В файле несколько организаторов: строки {organizer_rows}")

        # -----------------------------------
        # 3. Второй проход — запись в БД
        # -----------------------------------
        with transaction.atomic():
            # Создание группы с organizer_id из файла
            group, g_created = Group.objects.get_or_create(
                name=group_name,
                organizer_id=organizer_user.id
            )

            # Подгруппы
            created_subgroups = {}
            for mentor_tab, data in subgroup_plan.items():
                subgroup, created = Subgroup.objects.get_or_create(
                    group=group,
                    name=data["name"]
                )
                created_subgroups[mentor_tab] = subgroup

                if created:
                    result["created_subgroups"].append({
                        "mentor_tab": mentor_tab,
                        "subgroup_id": subgroup.id
                    })

            # Enrollment
            for item in enrollment_plan:
                user = item["user"]
                role = item["role"]
                mentor_tab = item["mentor_tab"]
                subgroup = (
                    created_subgroups[mentor_tab]
                    if mentor_tab and mentor_tab in created_subgroups
                    else None
                )
                row_num = item["excel_row"]

                enrollment, created = Enrollment.objects.get_or_create(
                    user=user,
                    subgroup=subgroup,
                    defaults={"role": role, "is_active": True}
                )

                if not created:
                    enrollment.role = role
                    enrollment.is_active = True
                    enrollment.save()

                result["enrollments"].append({
                    "tab_number": user.tab_number,
                    "role": role,
                    "mentor_tab": mentor_tab,
                    "subgroup_id": subgroup.id if subgroup else None,
                    "created": created
                })

        return result
