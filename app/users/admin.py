# your_app/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import AuthUser, Profile
from .forms import AuthUserCreationForm, AuthUserChangeForm


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Профиль'
    fk_name = 'user'


@admin.register(AuthUser)
class AuthUserAdmin(BaseUserAdmin):
    add_form = AuthUserCreationForm
    form = AuthUserChangeForm
    model = AuthUser

    list_display = ('tab_number', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_auth')
    list_filter = ('is_staff', 'is_active')

    fieldsets = (
        (None, {'fields': ('tab_number', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions', 'is_auth')}),
        # добавь разделы по-нужде
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('tab_number', 'first_name', 'last_name', 'email', 'password1', 'password2', 'is_staff', 'is_active')
        }),
    )

    inlines = (ProfileInline,)

    search_fields = ('tab_number', 'email', 'first_name', 'last_name')
    ordering = ('tab_number',)

    def get_account_role(self, obj):
        return obj.profile.account_role
    get_account_role.short_description = 'Роль аккаунта'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)
