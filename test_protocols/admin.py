from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.http import JsonResponse
from django.contrib import messages

from .models import (
    TestSuite,
    TestProtocol,
    ConnectionConfig,
    ProtocolRun,
    ProtocolResult,
    ResultAttachment,
    VerificationMethod
)


class TestProtocolInline(admin.TabularInline):
    """Inline admin for TestProtocol within TestSuite"""
    model = TestProtocol
    extra = 1
    fields = ('name', 'status', 'order_index', 'description')


@admin.register(TestSuite)
class TestSuiteAdmin(admin.ModelAdmin):
    """Admin for TestSuite model"""
    list_display = ('name', 'project', 'protocol_count', 'created_at')
    list_filter = ('project', 'created_at')
    search_fields = ('name', 'description', 'project__name')
    date_hierarchy = 'created_at'
    inlines = [TestProtocolInline]

    def protocol_count(self, obj):
        """Display the number of protocols in this suite"""
        count = obj.protocols.count()
        return format_html(
            '<a href="{}?suite__id__exact={}">{}</a>',
            reverse('admin:test_protocols_testprotocol_changelist'),
            obj.id,
            count
        )

    protocol_count.short_description = 'Protocols'


class ConnectionConfigInline(admin.StackedInline):
    """Inline admin for ConnectionConfig within TestProtocol"""
    model = ConnectionConfig
    can_delete = False
    fieldsets = (
        (None, {
            'fields': ('config_type',)
        }),
        (_('Connection Details'), {
            'fields': ('host', 'port', 'username', 'password', 'secret_key')
        }),
        (_('Connection Settings'), {
            'fields': ('timeout_seconds', 'retry_attempts')
        }),
        (_('Additional Configuration'), {
            'fields': ('config_data',),
            'classes': ('collapse',)
        }),
    )


class ProtocolRunInline(admin.TabularInline):
    """Inline admin for recent ProtocolRuns within TestProtocol"""
    model = ProtocolRun
    extra = 0
    fields = ('status', 'result_status', 'started_at', 'duration_seconds')
    readonly_fields = ('status', 'result_status', 'started_at', 'duration_seconds')
    ordering = ('-started_at',)
    max_num = 5
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(TestProtocol)
class TestProtocolAdmin(admin.ModelAdmin):
    """Admin for TestProtocol model"""
    list_display = ('name', 'suite', 'status', 'has_connection_config', 'last_run_status', 'order_index')
    list_filter = ('status', 'suite__project', 'suite')
    search_fields = ('name', 'description', 'suite__name')
    fieldsets = (
        (None, {
            'fields': ('suite', 'name', 'description', 'status')
        }),
        (_('Display Order'), {
            'fields': ('order_index',)
        }),
    )
    inlines = [ConnectionConfigInline, ProtocolRunInline]
    actions = ['run_protocols']

    def has_connection_config(self, obj):
        """Display whether this protocol has a connection config"""
        try:
            return bool(obj.connection_config)
        except ConnectionConfig.DoesNotExist:
            return False

    has_connection_config.boolean = True
    has_connection_config.short_description = 'Connection'

    def last_run_status(self, obj):
        """Display the status of the last run"""
        last_run = obj.runs.order_by('-started_at').first()
        if not last_run:
            return '-'

        status_colors = {
            'pass': 'green',
            'fail': 'red',
            'error': 'orange',
            'inconclusive': 'blue',
            'running': 'purple',
        }

        color = status_colors.get(last_run.result_status or 'inconclusive', 'gray')
        status = last_run.result_status or 'Not set'

        return format_html(
            '<a href="{}" style="color: {};">{}</a>',
            reverse('admin:your_app_protocolrun_change', args=[last_run.id]),
            color,
            status.capitalize()
        )

    last_run_status.short_description = 'Last Run'

    def run_protocols(self, request, queryset):
        """Admin action to run selected protocols"""
        if queryset.count() > 5:
            self.message_user(
                request,
                "You can only run up to 5 protocols at once.",
                level=messages.WARNING
            )
            return

        # Placeholder for actual protocol execution
        # In a real implementation, you would call your service to execute the protocols

        self.message_user(
            request,
            f"Successfully started {queryset.count()} protocols.",
            level=messages.SUCCESS
        )

    run_protocols.short_description = "Run selected protocols"


@admin.register(ConnectionConfig)
class ConnectionConfigAdmin(admin.ModelAdmin):
    """Admin for ConnectionConfig model"""
    list_display = ('protocol', 'config_type', 'host', 'port', 'test_connection_button')
    list_filter = ('config_type',)
    search_fields = ('protocol__name', 'host')
    fieldsets = (
        (None, {
            'fields': ('protocol', 'config_type')
        }),
        (_('Connection Details'), {
            'fields': ('host', 'port', 'username', 'password', 'secret_key')
        }),
        (_('Connection Settings'), {
            'fields': ('timeout_seconds', 'retry_attempts')
        }),
        (_('Additional Configuration'), {
            'fields': ('config_data',),
            'classes': ('collapse',)
        }),
    )
    raw_id_fields = ('protocol', 'username', 'password', 'secret_key')

    def test_connection_button(self, obj):
        """Display a button to test the connection"""
        return format_html(
            '<a class="button" onclick="testConnection({}); return false;">Test Connection</a>'
            '<script>function testConnection(id) {{'
            '  alert("Connection test functionality would be implemented here");'
            '}}</script>',
            obj.id
        )

    test_connection_button.short_description = 'Test'


class ResultAttachmentInline(admin.TabularInline):
    """Inline admin for ResultAttachment within ProtocolResult"""
    model = ResultAttachment
    extra = 1
    fields = ('name', 'file', 'content_type', 'description')


@admin.register(ProtocolRun)
class ProtocolRunAdmin(admin.ModelAdmin):
    """Admin for ProtocolRun model"""
    list_display = ('id', 'protocol', 'status', 'result_status', 'started_at', 'duration_display', 'executed_by')
    list_filter = ('status', 'result_status', 'protocol__suite', 'protocol__status')
    search_fields = ('protocol__name', 'executed_by')
    readonly_fields = ('started_at', 'completed_at', 'duration_seconds', 'created_at', 'updated_at')
    date_hierarchy = 'started_at'
    fieldsets = (
        (None, {
            'fields': ('protocol', 'status', 'result_status')
        }),
        (_('Execution Details'), {
            'fields': ('executed_by', 'started_at', 'completed_at', 'duration_seconds')
        }),
        (_('Error Information'), {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def duration_display(self, obj):
        """Format duration in a more readable way"""
        if obj.duration_seconds is None:
            return '-'

        # Format duration based on length
        if obj.duration_seconds < 1:
            return f"{int(obj.duration_seconds * 1000)} ms"
        elif obj.duration_seconds < 60:
            return f"{obj.duration_seconds:.2f} sec"
        else:
            minutes = int(obj.duration_seconds // 60)
            seconds = obj.duration_seconds % 60
            return f"{minutes}m {seconds:.1f}s"

    duration_display.short_description = 'Duration'

    def has_add_permission(self, request):
        """Disable adding runs directly from admin"""
        return False


@admin.register(ProtocolResult)
class ProtocolResultAdmin(admin.ModelAdmin):
    """Admin for ProtocolResult model"""
    list_display = ('id', 'run_protocol', 'success', 'has_error', 'created_at')
    list_filter = ('success', 'run__protocol__suite', 'run__status')
    search_fields = ('run__protocol__name', 'error_message')
    readonly_fields = ('run', 'created_at', 'updated_at', 'formatted_result_data')
    date_hierarchy = 'created_at'
    inlines = [ResultAttachmentInline]

    fieldsets = (
        (None, {
            'fields': ('run', 'success')
        }),
        (_('Result Data'), {
            'fields': ('formatted_result_data',),
            'classes': ('wide',)
        }),
        (_('Result Text'), {
            'fields': ('result_text',),
            'classes': ('wide',)
        }),
        (_('Error Information'), {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def run_protocol(self, obj):
        """Display the protocol name for this result"""
        return obj.run.protocol.name

    run_protocol.short_description = 'Protocol'

    def has_error(self, obj):
        """Display whether this result has an error message"""
        return bool(obj.error_message)

    has_error.boolean = True
    has_error.short_description = 'Has Error'

    def formatted_result_data(self, obj):
        """Format the JSON data for better display"""
        if not obj.result_data:
            return '-'

        import json
        try:
            formatted = json.dumps(obj.result_data, indent=2)
            return format_html('<pre>{}</pre>', formatted)
        except Exception:
            return str(obj.result_data)

    formatted_result_data.short_description = 'Result Data'

    def has_add_permission(self, request):
        """Disable adding results directly from admin"""
        return False


@admin.register(ResultAttachment)
class ResultAttachmentAdmin(admin.ModelAdmin):
    """Admin for ResultAttachment model"""
    list_display = ('name', 'result', 'content_type', 'created_at')
    list_filter = ('content_type', 'created_at')
    search_fields = ('name', 'description', 'result__run__protocol__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(VerificationMethod)
class VerificationMethodAdmin(admin.ModelAdmin):
    """Admin for VerificationMethod model"""
    list_display = ('name', 'method_type', 'supports_comparison', 'requires_expected_value')
    list_filter = ('method_type', 'supports_comparison', 'requires_expected_value')
    search_fields = ('name', 'description')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'method_type')
        }),
        (_('Comparison Settings'), {
            'fields': ('supports_comparison', 'comparison_method')
        }),
        (_('Value Requirements'), {
            'fields': ('requires_expected_value', 'supports_dynamic_expected')
        }),
        (_('Configuration'), {
            'fields': ('config_schema',),
            'classes': ('collapse',)
        }),
    )