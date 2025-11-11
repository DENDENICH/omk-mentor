# your_app/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import AuthUser

class AuthUserCreationForm(UserCreationForm):
    class Meta:
        model = AuthUser
        fields = (
            'tab_number', 
            'first_name', 
            'last_name', 
            'email',
        )

class AuthUserChangeForm(UserChangeForm):
    class Meta:
        model = AuthUser
        fields = (
            'tab_number', 
            'first_name',
            'last_name', 
            'email', 
            'is_active', 
            'is_staff',
            'is_auth',
        )
