from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.http import JsonResponse
from django.contrib import messages

# Add this to your existing admin.py file
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
import json

from .models import VerificationResult
from .models import (
    TestSuite,
    TestProtocol,
    ConnectionConfig,
    ProtocolRun,
    VerificationMethod,
    ExecutionStep,
)


class TestProtocolInline(admin.TabularInline):
    """Inline admin for TestProtocol within TestSuite"""

    model = TestProtocol
    extra = 1
    fields = ("name", "status", "order_index", "description")


@admin.register(TestSuite)
class TestSuiteAdmin(admin.ModelAdmin):
    """Admin for TestSuite model"""

    list_display = ("name", "project", "protocol_count", "created_at")
    list_filter = ("project", "created_at")
    search_fields = ("name", "description", "project__name")
    date_hierarchy = "created_at"
    inlines = [TestProtocolInline]

    def protocol_count(self, obj):
        """Display the number of protocols in this suite"""
        count = obj.protocols.count()
        return format_html(
            '<a href="{}?suite__id__exact={}">{}</a>',
            reverse("admin:test_protocols_testprotocol_changelist"),
            obj.id,
            count,
        )

    protocol_count.short_description = "Protocols"


class ConnectionConfigInline(admin.StackedInline):
    """Inline admin for ConnectionConfig within TestProtocol"""

    model = ConnectionConfig
    can_delete = False
    fieldsets = (
        (None, {"fields": ("config_type",)}),
        (
            _("Connection Details"),
            {"fields": ("host", "port", "username", "password", "secret_key")},
        ),
        (_("Connection Settings"), {"fields": ("timeout_seconds", "retry_attempts")}),
        (
            _("Additional Configuration"),
            {"fields": ("config_data",), "classes": ("collapse",)},
        ),
    )


class ProtocolRunInline(admin.TabularInline):
    """Inline admin for recent ProtocolRuns within TestProtocol"""

    model = ProtocolRun
    extra = 0
    fields = ("status", "result_status", "started_at", "duration_seconds")
    readonly_fields = ("status", "result_status", "started_at", "duration_seconds")
    ordering = ("-started_at",)
    max_num = 5
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class ExecutionStepInline(admin.TabularInline):
    """Inline admin for ExecutionStep within TestProtocol"""

    model = ExecutionStep
    extra = 1
    fields = ("formatted_args", "formatted_kwargs")
    readonly_fields = ("formatted_args", "formatted_kwargs")

    def formatted_args(self, obj):
        """Format args for better display"""
        if not obj.args:
            return "-"
        return format_html("<pre>{}</pre>", ", ".join(str(arg) for arg in obj.args))

    formatted_args.short_description = "Arguments"

    def formatted_kwargs(self, obj):
        """Format kwargs for better display"""
        if not obj.kwargs:
            return "-"

        formatted = "<br>".join([f"<b>{k}</b>: {v}" for k, v in obj.kwargs.items()])
        return format_html("<div>{}</div>", formatted)

    formatted_kwargs.short_description = "Keyword Arguments"


@admin.register(TestProtocol)
class TestProtocolAdmin(admin.ModelAdmin):
    """Admin for TestProtocol model"""

    list_display = (
        "name",
        "suite",
        "status",
        "has_connection_config",
        "has_execution_steps",
        "last_run_status",
        "order_index",
    )
    list_filter = ("status", "suite__project", "suite")
    search_fields = ("name", "description", "suite__name")
    fieldsets = (
        (None, {"fields": ("suite", "name", "description", "status")}),
        (_("Display Order"), {"fields": ("order_index",)}),
    )
    inlines = [ConnectionConfigInline, ExecutionStepInline, ProtocolRunInline]
    actions = ["run_protocols"]

    def has_connection_config(self, obj):
        """Display whether this protocol has a connection config"""
        try:
            return bool(obj.connection_config)
        except ConnectionConfig.DoesNotExist:
            return False

    has_connection_config.boolean = True
    has_connection_config.short_description = "Connection"

    def has_execution_steps(self, obj):
        """Display whether this protocol has execution steps"""
        return obj.steps.exists()

    has_execution_steps.boolean = True
    has_execution_steps.short_description = "Has Steps"

    def last_run_status(self, obj):
        """Display the status of the last run"""
        last_run = obj.runs.order_by("-started_at").first()
        if not last_run:
            return "-"

        status_colors = {
            "pass": "green",
            "fail": "red",
            "error": "orange",
            "inconclusive": "blue",
            "running": "purple",
        }

        color = status_colors.get(last_run.result_status or "inconclusive", "gray")
        status = last_run.result_status or "Not set"

        return format_html(
            '<a href="{}" style="color: {};">{}</a>',
            reverse("admin:test_protocols_protocolrun_change", args=[last_run.id]),
            color,
            status.capitalize(),
        )

    last_run_status.short_description = "Last Run"

    def run_protocols(self, request, queryset):
        """Admin action to run selected protocols"""
        if queryset.count() > 5:
            self.message_user(
                request,
                "You can only run up to 5 protocols at once.",
                level=messages.WARNING,
            )
            return

        # Placeholder for actual protocol execution
        # In a real implementation, you would call your service to execute the protocols

        self.message_user(
            request,
            f"Successfully started {queryset.count()} protocols.",
            level=messages.SUCCESS,
        )

    run_protocols.short_description = "Run selected protocols"


@admin.register(ConnectionConfig)
class ConnectionConfigAdmin(admin.ModelAdmin):
    """Admin for ConnectionConfig model"""

    list_display = ("protocol", "config_type", "test_connection_button")
    list_filter = ("config_type",)
    search_fields = ("protocol__name",)
    fieldsets = (
        (None, {"fields": ("protocol", "config_type")}),
        (_("Connection Settings"), {"fields": ("timeout_seconds", "retry_attempts")}),
        (
            _("Additional Configuration"),
            {"fields": ("config_data",), "classes": ("collapse",)},
        ),
    )
    raw_id_fields = ("protocol",)

    def test_connection_button(self, obj):
        """Display a button to test the connection"""
        return format_html(
            '<a class="button" onclick="testConnection({}); return false;">Test Connection</a>'
            "<script>function testConnection(id) {{"
            '  alert("Connection test functionality would be implemented here");'
            "}}</script>",
            obj.id,
        )

    test_connection_button.short_description = "Test"


@admin.register(ProtocolRun)
class ProtocolRunAdmin(admin.ModelAdmin):
    """Admin for ProtocolRun model"""

    list_display = (
        "id",
        "protocol",
        "status",
        "result_status",
        "started_at",
        "duration_display",
        "executed_by",
    )
    list_filter = ("status", "result_status", "protocol__suite", "protocol__status")
    search_fields = ("protocol__name", "executed_by")
    readonly_fields = (
        "started_at",
        "completed_at",
        "duration_seconds",
        "created_at",
        "updated_at",
    )
    date_hierarchy = "started_at"
    fieldsets = (
        (None, {"fields": ("protocol", "status", "result_status")}),
        (
            _("Execution Details"),
            {
                "fields": (
                    "executed_by",
                    "started_at",
                    "completed_at",
                    "duration_seconds",
                )
            },
        ),
        (
            _("Error Information"),
            {"fields": ("error_message",), "classes": ("collapse",)},
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def duration_display(self, obj):
        """Format duration in a more readable way"""
        if obj.duration_seconds is None:
            return "-"

        # Format duration based on length
        if obj.duration_seconds < 1:
            return f"{int(obj.duration_seconds * 1000)} ms"
        elif obj.duration_seconds < 60:
            return f"{obj.duration_seconds:.2f} sec"
        else:
            minutes = int(obj.duration_seconds // 60)
            seconds = obj.duration_seconds % 60
            return f"{minutes}m {seconds:.1f}s"

    duration_display.short_description = "Duration"

    def has_add_permission(self, request):
        """Disable adding runs directly from admin"""
        return False


@admin.register(VerificationMethod)
class VerificationMethodAdmin(admin.ModelAdmin):
    """Admin for VerificationMethod model"""

    list_display = (
        "name",
        "method_type",
        "supports_comparison",
        "requires_expected_value",
    )
    list_filter = ("method_type", "supports_comparison", "requires_expected_value")
    search_fields = ("name", "description")
    fieldsets = (
        ("Test Protocol Verification Method", {"fields": ("execution_step",)}),
        (None, {"fields": ("name", "description", "method_type")}),
        (
            _("Comparison Settings"),
            {"fields": ("supports_comparison", "comparison_method")},
        ),
        (
            _("Value Requirements"),
            {"fields": ("requires_expected_value", "supports_dynamic_expected")},
        ),
        (_("Configuration"), {"fields": ("config_schema",), "classes": ("collapse",)}),
    )


class ExecutionStepInline(admin.TabularInline):
    """Inline admin for ExecutionStep within TestProtocol"""

    model = ExecutionStep
    extra = 1
    fields = ("formatted_args", "formatted_kwargs")
    readonly_fields = ("formatted_args", "formatted_kwargs")

    def formatted_args(self, obj):
        """Format args for better display"""
        if not obj.args:
            return "-"
        return format_html("<pre>{}</pre>", ", ".join(str(arg) for arg in obj.args))

    formatted_args.short_description = "Arguments"

    def formatted_kwargs(self, obj):
        """Format kwargs for better display"""
        if not obj.kwargs:
            return "-"

        formatted = "<br>".join([f"<b>{k}</b>: {v}" for k, v in obj.kwargs.items()])
        return format_html("<div>{}</div>", formatted)

    formatted_kwargs.short_description = "Keyword Arguments"


@admin.register(ExecutionStep)
class ExecutionStepAdmin(admin.ModelAdmin):
    """Admin for ExecutionStep model"""

    list_display = (
        "id",
        "test_protocol",
        "formatted_args_short",
        "formatted_kwargs_short",
        "created_at",
    )
    list_filter = ("test_protocol__suite",)
    search_fields = ("test_protocol__name",)
    raw_id_fields = ("test_protocol",)

    fieldsets = (
        (None, {"fields": ("test_protocol", "name")}),
        (
            _("Execution Parameters"),
            {
                "fields": ("kwargs",),
                "description": "Define positional and keyword arguments for this execution step",
            },
        ),
    )

    def formatted_args_short(self, obj):
        """Format args for better display in list view"""
        if not obj.args:
            return "-"
        args_str = ", ".join(str(arg) for arg in obj.args)
        return args_str[:50] + "..." if len(args_str) > 50 else args_str

    formatted_args_short.short_description = "Arguments"

    def formatted_kwargs_short(self, obj):
        """Format kwargs for better display in list view"""
        if not obj.kwargs:
            return "-"

        kwargs_str = ", ".join([f"{k}: {v}" for k, v in obj.kwargs.items()])
        return kwargs_str[:50] + "..." if len(kwargs_str) > 50 else kwargs_str

    formatted_kwargs_short.short_description = "Keyword Arguments"


@admin.register(VerificationResult)
class VerificationResultAdmin(admin.ModelAdmin):
    """Admin for VerificationResult model"""

    list_display = (
        "id",
        "verification_step",
        "success_status",
        "verification_time_display",
        "method_type_display",
        "truncated_message",
    )
    list_filter = (
        "success",
        "status",
        "verification_step__method_type",
        "verification_time",
    )
    search_fields = ("verification_step__name", "message", "error_message")
    readonly_fields = (
        "verification_time",
        "formatted_result_data",
        "formatted_actual_value",
        "formatted_expected_value",
    )
    fieldsets = (
        (None, {"fields": ("verification_step", "success", "status")}),
        (
            "Verification Details",
            {
                "fields": (
                    "message",
                    "formatted_actual_value",
                    "formatted_expected_value",
                )
            },
        ),
        (
            "Error Information",
            {
                "fields": ("error_message", "error_stack_trace"),
                "classes": ("collapse",),
            },
        ),
        (
            "Result Data",
            {"fields": ("formatted_result_data",), "classes": ("collapse",)},
        ),
        ("Timestamps", {"fields": ("verification_time",), "classes": ("collapse",)}),
    )

    def success_status(self, obj):
        """Display success status with color"""
        if obj.success:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ PASS</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ FAIL</span>'
            )

    success_status.short_description = "Result"

    def verification_time_display(self, obj):
        """Format verification time for display"""
        return obj.verification_time.strftime("%Y-%m-%d %H:%M:%S")

    verification_time_display.short_description = "Time"
    verification_time_display.admin_order_field = "verification_time"

    def method_type_display(self, obj):
        """Display verification method type with styling"""
        method_type = (
            obj.verification_step.method_type if obj.verification_step else "Unknown"
        )

        # Define color mapping for different method types
        colors = {
            "string": "green",
            "numeric": "blue",
            "dict": "purple",
            "list": "orange",
            "api": "teal",
            "db": "indigo",
            "ssh": "red",
            "s3": "brown",
        }

        # Determine color based on method_type prefix
        color = "gray"
        for prefix, prefix_color in colors.items():
            if method_type.startswith(prefix):
                color = prefix_color
                break

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>', color, method_type
        )

    method_type_display.short_description = "Method Type"

    def truncated_message(self, obj):
        """Truncate message for display in list view"""
        if not obj.message:
            return "-"
        if len(obj.message) > 50:
            return obj.message[:47] + "..."
        return obj.message

    truncated_message.short_description = "Message"

    def formatted_result_data(self, obj):
        """Format result data as pretty-printed JSON"""
        if not obj.result_data:
            return "-"

        try:
            # If it's a string representation of JSON, parse it first
            if isinstance(obj.result_data, str):
                data = json.loads(obj.result_data)
            else:
                data = obj.result_data

            formatted_json = json.dumps(data, indent=2)
            return mark_safe(
                f'<pre style="max-height: 300px; overflow: auto;">{formatted_json}</pre>'
            )
        except Exception as e:
            return f"Error formatting JSON: {str(e)}"

    formatted_result_data.short_description = "Result Data"

    def formatted_actual_value(self, obj):
        """Format actual value for display"""
        if obj.actual_value is None:
            return "-"

        try:
            if isinstance(obj.actual_value, (dict, list)):
                formatted_value = json.dumps(obj.actual_value, indent=2)
                return mark_safe(
                    f'<pre style="max-height: 200px; overflow: auto;">{formatted_value}</pre>'
                )
            return str(obj.actual_value)
        except Exception:
            return str(obj.actual_value)

    formatted_actual_value.short_description = "Actual Value"

    def formatted_expected_value(self, obj):
        """Format expected value for display"""
        if obj.expected_value is None:
            return "-"

        try:
            if isinstance(obj.expected_value, (dict, list)):
                formatted_value = json.dumps(obj.expected_value, indent=2)
                return mark_safe(
                    f'<pre style="max-height: 200px; overflow: auto;">{formatted_value}</pre>'
                )
            return str(obj.expected_value)
        except Exception:
            return str(obj.expected_value)

    formatted_expected_value.short_description = "Expected Value"
