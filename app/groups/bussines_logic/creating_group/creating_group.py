from collections import defaultdict
from typing import NamedTuple, cast

from django.db import transaction

from groups.models import Group, Subgroup
from learning.models import Enrollment
from users.models import AuthUser

from groups.exceptions import FileException, InvalidDataException
from groups.bussines_logic.creating_group.items import ImportData

class Users(NamedTuple):
    organizer: AuthUser
    students: defaultdict[str, defaultdict[str, AuthUser]]
    mentors: defaultdict[str, AuthUser]



class GroupCreatingService:
    """
    Class for creating group from JSON schema
    """

    def import_json(self, schema: ImportData):

        group_name = schema["group_name"]
        organizer_tab = schema["organizer"]["tab"]
        members = schema["members"]

        users = self._getting_user(organizer_tab, members)

        with transaction.atomic():
            
            group = self._creating_group(users.organizer, group_name)

            self._creating_subgroup(group, users.mentors, users.students)
            

    
    def _getting_user(self, organizer_tab: str, members: list) -> Users:
        students_cache = defaultdict(defaultdict)
        mentors_cache = defaultdict(AuthUser)

        try:
            organizer = AuthUser.objects.get(tab_number=organizer_tab)
        except AuthUser.DoesNotExist:
            raise InvalidDataException(f"Организатор {organizer_tab} не найден")
        if self._is_profile_role(organizer, ("admin",)):
            raise InvalidDataException(f"Администратор {organizer_tab} не может быть организатором")
        
        for m in members:
            tab = m["tab"]
            try:
                # на оптимизацию извлечение профиля
                user = AuthUser.objects.get(tab_number=tab)
            except AuthUser.DoesNotExist:
                raise InvalidDataException(f"Пользователь {tab} не найден")
            
            if self._is_profile_role(user, ("admin", "organizer")):
                raise InvalidDataException(
                    f"{tab} не может быть участником, поскольку уже является организатором или администратором"
                )
            
            if m["role"] == "student" and m.get("mentor_tab"):
                students_by_mentor_tab = students_cache.get(m["mentor_tab"])
                if not students_by_mentor_tab:
                    students_by_mentor_tab = defaultdict(AuthUser)
                    students_cache[m["mentor_tab"]] = students_by_mentor_tab
                students_by_mentor_tab[tab] = user
            elif m["role"] == "mentor":
                mentors_cache[tab] = user
            else:
                raise InvalidDataException(f"Неверная роль {m['role']} для пользователя {tab}")
        
        return Users(organizer, students_cache, mentors_cache)
            

    def _is_profile_role(self, user: AuthUser, roles: tuple[str, ...]) -> bool:
        account_role = user.profile.account_role
        return account_role in roles


    def _creating_group(self, organizer: AuthUser, group_name: str) -> Group:
        group, _ = Group.objects.get_or_create(
                name=group_name,
                organizer=organizer
            )
        return group
    
    def _creating_subgroup(
            self, 
            group: Group, 
            mentors: defaultdict[str, AuthUser],
            students: defaultdict[str, defaultdict[str, AuthUser]]
        ) -> None:
        for mentor_tab, mentor in mentors.items():
            subgroup, created = Subgroup.objects.get_or_create(
                mentor=mentor,
                group=group,
                name=f"{group.name}-{mentor.first_name} {mentor.last_name}"
            )

            if created:
                students_by_mentor_tab: defaultdict[str, AuthUser] = cast(defaultdict[str, AuthUser], students.get(mentor_tab))
                self._creating_students_enrollments_with_subgroup(
                    students=students_by_mentor_tab,
                    subgroup=subgroup
                )
    
    def _creating_students_enrollments_with_subgroup(
            self,
            students: defaultdict[str, AuthUser],
            subgroup: Subgroup,
        ) -> None:
        for student_tab, student in students.items():

            Enrollment.objects.get_or_create(
                user=student,
                subgroup=subgroup,
                role="student",
            )
