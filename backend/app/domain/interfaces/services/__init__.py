"""Service interface definitions."""

from .EmailServiceInterface import EmailServiceInterface
from .FileUploadServiceInterface import FileUploadServiceInterface
from .OAuthServiceInterface import OAuthServiceInterface

__all__ = [
    "EmailServiceInterface",
    "OAuthServiceInterface",
    "FileUploadServiceInterface",
]
