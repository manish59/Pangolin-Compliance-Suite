from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect

from .models import (
    TestSuite, TestProtocol, ConnectionConfig, ProtocolRun,
    ProtocolResult, ResultAttachment, VerificationMethod
)


# TestSuite Views
class TestSuiteListView(ListView):
    model = TestSuite
    template_name = 'test_protocols/testsuite_list.html'
    context_object_name = 'testsuites'
    paginate_by = 10


class TestSuiteDetailView(DetailView):
    model = TestSuite
    template_name = 'test_protocols/testsuite_detail.html'
    context_object_name = 'testsuite'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['protocols'] = self.object.get_ordered_protocols()
        return context


class TestSuiteCreateView(CreateView):
    model = TestSuite
    template_name = 'test_protocols/testsuite_form.html'
    fields = ['name', 'description', 'project']

    def get_success_url(self):
        return reverse('testsuite:testsuite_detail', kwargs={'pk': self.object.pk})


class TestSuiteUpdateView(UpdateView):
    model = TestSuite
    template_name = 'test_protocols/testsuite_form.html'
    fields = ['name', 'description', 'project']

    def get_success_url(self):
        return reverse('testsuite:testsuite_detail', kwargs={'pk': self.object.pk})


# TestProtocol Views
class TestProtocolListView(ListView):
    model = TestProtocol
    template_name = 'test_protocols/protocol_list.html'
    context_object_name = 'protocols'
    paginate_by = 10


class TestProtocolDetailView(DetailView):
    model = TestProtocol
    template_name = 'test_protocols/protocol_detail.html'
    context_object_name = 'protocol'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['runs'] = self.object.runs.all().order_by('-started_at')[:5]
        try:
            context['connection_config'] = self.object.connection_config
        except ConnectionConfig.DoesNotExist:
            context['connection_config'] = None
        return context


class TestProtocolCreateView(CreateView):
    model = TestProtocol
    template_name = 'test_protocols/protocol_form.html'
    fields = ['suite', 'name', 'description', 'status', 'order_index']

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Pre-select suite if passed in URL
        suite_id = self.kwargs.get('suite_id')
        if suite_id:
            form.initial['suite'] = suite_id
        return form

    def form_valid(self, form):
        # Set suite if it's in the URL
        suite_id = self.kwargs.get('suite_id')
        if suite_id:
            form.instance.suite = get_object_or_404(TestSuite, pk=suite_id)
        suite = form.instance.suite
        name = form.instance.name
        if TestProtocol.objects.filter(suite=suite, name=name).exists():
            form.add_error('name', 'A protocol with this name already exists in this suite.')
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('testsuite:protocol_detail', kwargs={'pk': self.object.pk})


class TestProtocolCreateFromSuiteView(TestProtocolCreateView):
    fields = ['name', 'description', 'status', 'order_index']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        suite_id = self.kwargs.get('suite_id')
        if suite_id:
            context['suite'] = get_object_or_404(TestSuite, pk=suite_id)
        return context

    def get_success_url(self):
        # Redirect back to the suite detail page after creation
        suite_id = self.kwargs.get('suite_id')
        if suite_id:
            return reverse('testsuite:testsuite_detail', kwargs={'pk': suite_id})
        return super().get_success_url()


class TestProtocolUpdateView(UpdateView):
    model = TestProtocol
    template_name = 'test_protocols/protocol_form.html'
    fields = ['name', 'description', 'status', 'order_index', 'suite']

    def get_success_url(self):
        return reverse('testsuite:protocol_detail', kwargs={'pk': self.object.pk})


# ConnectionConfig Views
class ConnectionConfigListView(ListView):
    model = ConnectionConfig
    template_name = 'test_protocols/connection_list.html'
    context_object_name = 'connections'
    paginate_by = 10


class ConnectionConfigDetailView(DetailView):
    model = ConnectionConfig
    template_name = 'test_protocols/connection_detail.html'
    context_object_name = 'connection'


class ConnectionConfigCreateView(CreateView):
    model = ConnectionConfig
    template_name = 'test_protocols/connection_form.html'
    fields = ['config_type', 'host', 'port', 'username', 'password',
              'secret_key', 'timeout_seconds', 'retry_attempts', 'config_data']

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Pre-select protocol if passed in URL
        protocol_id = self.kwargs.get('protocol_id')
        if protocol_id:
            form.initial['protocol'] = protocol_id
        return form

    def form_valid(self, form):
        # Set protocol if it's in the URL
        protocol_id = self.kwargs.get('protocol_id')
        if protocol_id:
            form.instance.protocol = get_object_or_404(TestProtocol, pk=protocol_id)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('testsuite:connection_detail', kwargs={'pk': self.object.pk})


class ConnectionConfigUpdateView(UpdateView):
    model = ConnectionConfig
    template_name = 'test_protocols/connection_form.html'
    fields = ['protocol', 'config_type', 'host', 'port', 'username', 'password',
              'secret_key', 'timeout_seconds', 'retry_attempts', 'config_data']

    def get_success_url(self):
        return reverse('testsuite:connection_detail', kwargs={'pk': self.object.pk})


# ProtocolRun Views
class ProtocolRunListView(ListView):
    model = ProtocolRun
    template_name = 'test_protocols/run_list.html'
    context_object_name = 'runs'
    paginate_by = 10


class ProtocolRunDetailView(DetailView):
    model = ProtocolRun
    template_name = 'test_protocols/run_detail.html'
    context_object_name = 'run'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['result'] = self.object.result
        except ProtocolResult.DoesNotExist:
            context['result'] = None
        return context


class ProtocolRunCreateView(CreateView):
    model = ProtocolRun
    template_name = 'test_protocols/run_form.html'
    fields = ['executed_by', 'status', 'result_status', 'error_message']

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Pre-select protocol if passed in URL
        protocol_id = self.kwargs.get('protocol_id')
        if protocol_id:
            form.initial['protocol'] = protocol_id
        return form

    def form_valid(self, form):
        # Set protocol if it's in the URL
        protocol_id = self.kwargs.get('protocol_id')
        if protocol_id:
            form.instance.protocol = get_object_or_404(TestProtocol, pk=protocol_id)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('testsuite:run_detail', kwargs={'pk': self.object.pk})


class ProtocolRunUpdateView(UpdateView):
    model = ProtocolRun
    template_name = 'test_protocols/run_form.html'
    fields = ['protocol', 'executed_by', 'completed_at', 'status', 'result_status',
              'error_message', 'duration_seconds']

    def get_success_url(self):
        return reverse('testsuite:run_detail', kwargs={'pk': self.object.pk})


# ProtocolResult Views
class ProtocolResultListView(ListView):
    model = ProtocolResult
    template_name = 'test_protocols/result_list.html'
    context_object_name = 'results'
    paginate_by = 10


class ProtocolResultDetailView(DetailView):
    model = ProtocolResult
    template_name = 'test_protocols/result_detail.html'
    context_object_name = 'result'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['attachments'] = self.object.attachments.all()
        return context


class ProtocolResultCreateView(CreateView):
    model = ProtocolResult
    template_name = 'test_protocols/result_form.html'
    fields = ['success', 'result_data', 'result_text', 'error_message']

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Pre-select run if passed in URL
        run_id = self.kwargs.get('run_id')
        if run_id:
            form.initial['run'] = run_id
        return form

    def form_valid(self, form):
        # Set run if it's in the URL
        run_id = self.kwargs.get('run_id')
        if run_id:
            form.instance.run = get_object_or_404(ProtocolRun, pk=run_id)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('testsuite:result_detail', kwargs={'pk': self.object.pk})


class ProtocolResultUpdateView(UpdateView):
    model = ProtocolResult
    template_name = 'test_protocols/result_form.html'
    fields = ['run', 'success', 'result_data', 'result_text', 'error_message']

    def get_success_url(self):
        return reverse('testsuite:result_detail', kwargs={'pk': self.object.pk})


# ResultAttachment Views
class ResultAttachmentListView(ListView):
    model = ResultAttachment
    template_name = 'test_protocols/attachment_list.html'
    context_object_name = 'attachments'
    paginate_by = 10


class ResultAttachmentDetailView(DetailView):
    model = ResultAttachment
    template_name = 'test_protocols/attachment_detail.html'
    context_object_name = 'attachment'


class ResultAttachmentCreateView(CreateView):
    model = ResultAttachment
    template_name = 'test_protocols/attachment_form.html'
    fields = ['name', 'description', 'file', 'content_type']

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Pre-select result if passed in URL
        result_id = self.kwargs.get('result_id')
        if result_id:
            form.initial['result'] = result_id
        return form

    def form_valid(self, form):
        # Set result if it's in the URL
        result_id = self.kwargs.get('result_id')
        if result_id:
            form.instance.result = get_object_or_404(ProtocolResult, pk=result_id)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('testsuite:attachment_detail', kwargs={'pk': self.object.pk})


class ResultAttachmentUpdateView(UpdateView):
    model = ResultAttachment
    template_name = 'test_protocols/attachment_form.html'
    fields = ['result', 'name', 'description', 'file', 'content_type']

    def get_success_url(self):
        return reverse('testsuite:attachment_detail', kwargs={'pk': self.object.pk})


# VerificationMethod Views
class VerificationMethodListView(ListView):
    model = VerificationMethod
    template_name = 'test_protocols/verification_list.html'
    context_object_name = 'verifications'
    paginate_by = 10


class VerificationMethodDetailView(DetailView):
    model = VerificationMethod
    template_name = 'test_protocols/verification_detail.html'
    context_object_name = 'verification'


class VerificationMethodCreateView(CreateView):
    model = VerificationMethod
    template_name = 'test_protocols/verification_form.html'
    fields = ['name', 'description', 'method_type', 'supports_comparison',
              'comparison_method', 'config_schema', 'requires_expected_value',
              'supports_dynamic_expected']

    def get_success_url(self):
        return reverse('testsuite:verification_detail', kwargs={'pk': self.object.pk})


class VerificationMethodUpdateView(UpdateView):
    model = VerificationMethod
    template_name = 'test_protocols/verification_form.html'
    fields = ['name', 'description', 'method_type', 'supports_comparison',
              'comparison_method', 'config_schema', 'requires_expected_value',
              'supports_dynamic_expected']

    def get_success_url(self):
        return reverse('testsuite:verification_detail', kwargs={'pk': self.object.pk})