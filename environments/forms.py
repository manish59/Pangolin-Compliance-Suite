from django import forms
from .models import Environment, VARIABLE_TYPES


class EnvironmentForm(forms.ModelForm):
    """
    Custom form for Environment model to handle value setting
    """
    # Add field for file uploads
    uploaded_file = forms.FileField(
        required=False,
        help_text="Upload a file for file-type variables"
    )

    # Add a field for inputting values that isn't the direct model field
    raw_value = forms.CharField(
        label="Value",
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text="Enter the raw value. For secret types, this will be encrypted."
    )

    class Meta:
        model = Environment
        fields = ['project', 'key', 'variable_type', 'description', 'is_enabled']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')

        # If we have an instance, pre-populate raw_value with the actual value
        if instance:
            self.initial['raw_value'] = instance.get_actual_value()

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Set the value with encryption if needed
        raw_value = self.cleaned_data.get('raw_value', '')
        instance.set_value(raw_value)

        # Handle file upload for file type
        if instance.variable_type == 'file' and 'uploaded_file' in self.files:
            uploaded_file = self.files['uploaded_file']
            instance.set_file_content(uploaded_file)

        if commit:
            instance.save()

        return instance


class EnvironmentToggleForm(forms.Form):
    """
    Form for toggling the enabled status of an environment variable
    """
    confirm = forms.BooleanField(
        required=True,
        widget=forms.HiddenInput,
        initial=True
    )