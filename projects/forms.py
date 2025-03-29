from django.forms import ModelForm
from .models import Project


class ProjectForm(ModelForm):
    """Form for Project creation and updating"""

    class Meta:
        model = Project
        fields = ["name", "description", "is_active"]
