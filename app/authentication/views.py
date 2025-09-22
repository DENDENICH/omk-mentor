from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.request import Request
from django.shortcuts import render


def view(request: Request) -> Response:
    return Response({"status": True})
