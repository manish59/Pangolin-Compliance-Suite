# environments/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django import forms

from .models import Environment, VARIABLE_TYPES


class EnvironmentAdminForm(forms.ModelForm):
    """
    Custom form for EnvironmentVariable admin to handle value setting
    """
    # Add a field for inputting values that isn't the direct model field
    raw_value = forms.CharField(
        label="Value",
        widget=forms.Textarea,
        required=False,
        help_text="Enter the raw value. For secret types, this will be encrypted."
    )

    class Meta:
        model = Environment
        fields = ['project', 'key', 'raw_value', 'variable_type', 'description', 'is_enabled']


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

        if commit:
            instance.save()

        return instance


@admin.register(Environment)
class EnvironmentAdmin(admin.ModelAdmin):
    form = EnvironmentAdminForm
    list_display = ('key', 'display_value_truncated', 'variable_type_colored',
                    'project_link', 'is_enabled', 'created_at', 'updated_at')
    list_filter = ('variable_type', 'is_enabled', 'project')
    search_fields = ('key', 'description', 'project__name')
    readonly_fields = ('id', 'created_at', 'updated_at', '_is_encrypted')

    fieldsets = (
        (None, {
            'fields': ('project', 'key', 'raw_value', 'variable_type')
        }),
        ('Settings', {
            'fields': ('description', 'is_enabled')
        }),
        ('Advanced', {
            'classes': ('collapse',),
            'fields': ('id', '_is_encrypted', 'created_at', 'updated_at'),
        }),
    )

    def display_value_truncated(self, obj):
        """Display a truncated or masked value"""
        if obj.variable_type == 'secret':
            return '••••••••••' if obj.value else ''

        value = obj.get_actual_value()
        if len(value) > 50:
            return value[:47] + '...'
        return value

    display_value_truncated.short_description = 'Value'

    def variable_type_colored(self, obj):
        """Display variable type with color coding"""
        colors = {
            'text': '#6c757d',  # Gray
            'number': '#28a745',  # Green
            'boolean': '#fd7e14',  # Orange
            'secret': '#dc3545',  # Red
            'json': '#17a2b8',  # Teal
            'url': '#007bff',  # Blue
        }

        color = colors.get(obj.variable_type, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_variable_type_display()
        )

    variable_type_colored.short_description = 'Type'

    def project_link(self, obj):
        """Link to the project admin"""
        url = reverse('admin:projects_project_change', args=[obj.project.id])
        return format_html('<a href="{}">{}</a>', url, obj.project.name)

    project_link.short_description = 'Project'

    def save_model(self, request, obj, form, change):
        """Handle saving the model with encryption"""
        # Model saving is handled by the custom form
        super().save_model(request, obj, form, change)