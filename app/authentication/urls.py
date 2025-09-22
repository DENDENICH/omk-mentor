from django.urls import path
from .views import view

app_name = "authentication"

urlpatterns = [
    path("view/", view, name="view")
]