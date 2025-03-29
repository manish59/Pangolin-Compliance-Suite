# environments/services/encryption.py
from cryptography.fernet import Fernet
from django.conf import settings


# Get the encryption key from settings or generate a new one
def get_encryption_key():
    """
    Retrieves the encryption key from settings or generates a new one.

    In production, this key should be set in the environment variables
    and never stored in the code or version control.
    """
    key = getattr(settings, "ENCRYPTION_KEY", None)

    return key


def encrypt_value(value):
    """
    Encrypts a string value using Fernet symmetric encryption.

    Args:
        value (str): The value to encrypt

    Returns:
        str: The encrypted value as a base64 string
    """
    if not value:
        return ""

    # Convert string to bytes if needed
    if isinstance(value, str):
        value = value.encode("utf-8")

    # Initialize the Fernet cipher with our key
    fernet = Fernet(get_encryption_key())

    # Encrypt the value
    encrypted_value = fernet.encrypt(value)

    # Return as a base64 string
    return encrypted_value.decode("utf-8")


def decrypt_value(encrypted_value):
    """
    Decrypts a Fernet-encrypted value.

    Args:
        encrypted_value (str): The encrypted value to decrypt

    Returns:
        str: The decrypted value as a string
    """
    if not encrypted_value:
        return ""

    # Convert to bytes if needed
    if isinstance(encrypted_value, str):
        encrypted_value = encrypted_value.encode("utf-8")

    # Initialize the Fernet cipher with our key
    fernet = Fernet(get_encryption_key())

    try:
        # Decrypt the value
        decrypted_value = fernet.decrypt(encrypted_value)

        # Return as a string
        return decrypted_value.decode("utf-8")
    except Exception as e:
        # Handle decryption errors
        print(f"Decryption error: {e}")
        return ""
