# environments/models/environment_variable.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from engine.models import BaseModel
from projects.models import Project
from utils.encryption import encrypt_value, decrypt_value

VARIABLE_TYPES = [
    ('text', 'Text'),
    ('number', 'Number'),
    ('boolean', 'Boolean'),
    ('secret', 'Secret'),  # This type will be encrypted
    ('json', 'JSON'),
    ('url', 'URL'),
    ('file', 'File'),  # New file type
]


class Environment(BaseModel):
    """
    Model representing a key-value pair in an environment.
    Secret type values will be automatically encrypted.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='environments',
        help_text="Environment this variable belongs to"
    )
    key = models.CharField(
        _("Key"),
        max_length=100,
        help_text="Variable name or key"
    )
    value = models.TextField(
        _("Value"),
        help_text="Variable value (may be encrypted for secret type)"
    )
    variable_type = models.CharField(
        _("Type"),
        max_length=20,
        choices=VARIABLE_TYPES,
        default='text',
        help_text="Type of this variable"
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text="Optional description of this variable"
    )
    is_enabled = models.BooleanField(
        _("Enabled"),
        default=True,
        help_text="Whether this variable is enabled"
    )

    # Internal storage for encrypted values
    _is_encrypted = models.BooleanField(
        _("Is Encrypted"),
        default=False,
        help_text="Whether this value is currently encrypted"
    )
    file_content = models.BinaryField(
        blank=True,
        null=True,
        help_text="Binary content of uploaded file"
    )
    file_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Original filename of uploaded file"
    )
    file_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="MIME type of uploaded file"
    )

    class Meta:
        ordering = ['key']
        verbose_name = _("Environment")
        verbose_name_plural = _("Environment")
        # Ensure variable names are unique per environment
        unique_together = ['project', 'key']

    def __str__(self):
        status = "(secret)" if self.variable_type == 'secret' else ""
        return f"{self.key}{status} - {self.project.name}"

    @property
    def display_value(self):
        """
        Get a displayable value - decrypt if needed and mask secrets
        """
        # For file type, show filename
        if self.variable_type == 'file':
            return self.file_name or "No file uploaded"

        # For secret type, return a masked value
        if self.variable_type == 'secret':
            if self.value:
                return "••••••••••"
            return ""

        # For other types, return the actual value
        return self.get_actual_value()

    def set_file_content(self, file_obj):
        """Set file content from a file object"""
        if file_obj:
            content = file_obj.read()
            self.file_content = content
            self.file_name = file_obj.name
            self.file_type = getattr(file_obj, 'content_type', None)

    def get_actual_value(self):
        """
        Get the actual value, decrypting if needed
        """
        # For file type, return file content
        if self.variable_type == 'file':
            return self.file_content

        # If encrypted, decrypt the value
        if self._is_encrypted:
            try:
                decrypted_value = decrypt_value(self.value)
            except Exception as e:
                # On decryption error, return empty string
                print(f"Decryption error for variable {self.key}: {e}")
                return ""
        else:
            # Otherwise use the value as is
            decrypted_value = self.value

        return decrypted_value

    def get_typed_value(self):
        """
        Get the value converted to its appropriate type based on variable_type

        Returns:
            The value in the appropriate Python type:
            - text: str
            - number: int or float
            - boolean: bool
            - secret: str (decrypted)
            - json: dict or list (parsed JSON)
            - url: str
        """
        # First get the actual string value (decrypted if needed)
        raw_value = self.get_actual_value()

        # If empty, return appropriate default value based on type
        if not raw_value:
            if self.variable_type == 'number':
                return 0
            elif self.variable_type == 'boolean':
                return False
            elif self.variable_type == 'json':
                return {}
            else:
                return ""

        # Convert based on variable type
        try:
            if self.variable_type == 'number':
                # Try to convert to int first, then float if that fails
                try:
                    return int(raw_value)
                except ValueError:
                    return float(raw_value)

            elif self.variable_type == 'boolean':
                # Convert various string representations to boolean
                return raw_value.lower() in ('true', 'yes', '1', 't', 'y')

            elif self.variable_type == 'json':
                import json
                return json.loads(raw_value)

            else:
                # For text, secret, url, and any other types, return as string
                return raw_value

        except Exception as e:
            # On conversion error, log and return the raw value
            print(f"Error converting value for {self.key} to {self.variable_type}: {e}")
            return raw_value

    def set_value(self, value):
        """
        Set the value, encrypting if needed
        """
        # For file type, handle separately
        if self.variable_type == 'file':
            # If value is a file object, use set_file_content
            if hasattr(value, 'read'):
                self.set_file_content(value)
            return

        # Convert to string if not already
        if not isinstance(value, str):
            value = str(value)

        # For secret type, encrypt the value
        if self.variable_type == 'secret':
            self.value = encrypt_value(value)
            self._is_encrypted = True
        else:
            # For non-secret types, store as plain text
            self.value = value
            self._is_encrypted = False

    def clean(self):
        """Validate the variable"""
        # Ensure key doesn't contain spaces or special characters
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', self.key):
            raise ValidationError({'key': _(
                "Key must contain only letters, numbers, and underscores."
            )})

        # Check for duplicate keys in the same environment
        duplicates = Environment.objects.filter(
            project=self.project,
            key__iexact=self.key
        )

        # If this is an update, exclude the current instance
        if self.pk:
            duplicates = duplicates.exclude(pk=self.pk)

        if duplicates.exists():
            raise ValidationError({'key': _(
                "This environment already has a variable with this key."
            )})

    def save_model(self, request, obj, form, change):
        """
        Override save_model to handle the error case when the object doesn't exist yet
        """
        if change:  # If this is an update (not creation)
            try:
                # Get the original object
                original = Environment.objects.get(pk=obj.pk)

                # If type changed to or from secret, handle encryption/decryption
                if original.variable_type != obj.variable_type:
                    # Get the current actual value
                    value = original.get_actual_value()

                    # Store with appropriate encryption
                    obj.set_value(value)
            except Environment.DoesNotExist:
                # If this is actually a new object despite 'change' being True
                # Just set the value with proper encryption
                obj.set_value(obj.value)
        else:
            # For new objects, ensure the value is set properly
            obj.set_value(obj.value)

        # Continue with normal save
        super().save_model(request, obj, form, change)

    def get_variables_dict(self):
        """
        Get all environment variables as a dictionary with raw string values.
        This is useful for test execution.
        """
        variables = {}
        for var in self.environments.filter(is_enabled=True):
            variables[var.key] = var.get_actual_value()
        return variables