
import os

from cryptography.fernet import Fernet, InvalidToken
from django.core.exceptions import ImproperlyConfigured


def get_fernet():
    key = os.environ.get("FERNET_KEY")

    if not key or key == "TU_CLAVE_GENERADA":
        raise ImproperlyConfigured(
            "La variable de entorno FERNET_KEY no está configurada."
        )

    try:
        return Fernet(key.encode())
    except (ValueError, TypeError):
        raise ImproperlyConfigured(
            "La variable FERNET_KEY no tiene un formato válido."
        )


def encrypt_totp_secret(secret):
    if not secret:
        return ""

    return get_fernet().encrypt(secret.encode()).decode()


def decrypt_totp_secret(encrypted_secret):
    if not encrypted_secret:
        return ""

    try:
        return get_fernet().decrypt(
            encrypted_secret.encode()
        ).decode()
    except InvalidToken:
        raise ImproperlyConfigured(
            "No se pudo descifrar la clave TOTP. "
            "Comprueba que FERNET_KEY sea la misma con la que se cifró."
        )
