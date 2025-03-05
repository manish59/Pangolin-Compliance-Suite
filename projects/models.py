from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from engine.models import BaseModel


class Project(BaseModel):
    """
    Model representing a test automation project.
    Inherits id, created_at and updated_at from BaseModel.
    """
    name = models.CharField(
        _("Project Name"),
        max_length=100,
        help_text="Name of the test automation project"
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text="Detailed description of the project and its purpose"
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='projects',
        help_text="User who owns this project"
    )
    is_active = models.BooleanField(
        _("Active"),
        default=True,
        help_text="Whether this project is currently active"
    )

    class Meta:
        ordering = ['-updated_at']
        verbose_name = _("Project")
        verbose_name_plural = _("Projects")
        # Ensure project names are unique per user
        unique_together = ['name', 'owner']

    def __str__(self):
        return f"{self.name}"

    def clean(self, *args, **kwargs):
        """Validate project data"""
        # Ensure project name is not too short
        if len(self.name.strip()) < 3:
            raise ValidationError({'name': _("Project name must be at least 3 characters.")})

        # Check for duplicate projects with the same name for this user
        if self.owner_id is not None:
            duplicate_projects = Project.objects.filter(
                name__iexact=self.name,
                owner=self.owner
            )

            # If this is an update, exclude the current instance
            if self.pk:
                duplicate_projects = duplicate_projects.exclude(pk=self.pk)

            if duplicate_projects.exists():
                raise ValidationError({'name': _("You already have a project with this name.")})

    def save(self, *args, **kwargs):
        """Override save to perform validation"""
        self.clean(*args, **kwargs)
        return super().save(*args, **kwargs)