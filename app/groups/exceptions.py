from rest_framework import status

class CustomException(BaseException):
    code: int

class FileException(CustomException):
    code = status.HTTP_500_INTERNAL_SERVER_ERROR

class InvalidDataException(CustomException):
    code = status.HTTP_400_BAD_REQUEST