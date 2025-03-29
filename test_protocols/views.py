import json
import yaml
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.views import View
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.utils.safestring import mark_safe
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseForbidden
from django.contrib import messages
from django.db import transaction
from .models import (
    TestProtocol, VerificationMethod, VERIFICATION_METHOD_CHOICES,
    COMPARISON_OPERATOR_CHOICES
)
from environments.models import Environment
from .models import ExecutionStep, TestProtocol, ProtocolRun
from .models import (
    TestSuite, TestProtocol, ConnectionConfig, ProtocolRun, VerificationMethod, ExecutionStep
)
from test_protocols.services import run_protocol, run_suite


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
    fields = ['protocol', 'config_type',
              'timeout_seconds', 'retry_attempts', 'config_data']

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Pre-select protocol if passed in URL
        protocol_id = self.kwargs.get('protocol_id')
        if protocol_id:
            try:
                test_protocol = TestProtocol.objects.get(pk=protocol_id)
                form.initial['protocol'] = protocol_id
            except TestProtocol.DoesNotExist:
                pass
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        protocol_id = self.kwargs.get('protocol_id')
        context['field_name'] = 'config_data'
        if protocol_id:
            try:
                test_protocol = TestProtocol.objects.get(pk=protocol_id)
                project = test_protocol.suite.project
                context['environments'] = Environment.objects.filter(project=project)
                context['existing_connections'] = ConnectionConfig.objects.filter(protocol__suite=test_protocol.suite)
            except (TestProtocol.DoesNotExist, Environment.DoesNotExist):
                context['environments'] = None
                context['existing_connections'] = ConnectionConfig.objects.none()
        return context

    def post(self, request, *args, **kwargs):
        # Check if using an existing connection
        selected_connection_id = request.POST.get('selected_connection_id')
        if selected_connection_id:
            try:
                # Get the existing connection
                existing_connection = ConnectionConfig.objects.get(pk=selected_connection_id)

                # Get the protocol
                protocol_id = self.kwargs.get('protocol_id')
                if protocol_id:
                    protocol = get_object_or_404(TestProtocol, pk=protocol_id)

                    # Create a new connection with the same configuration
                    new_connection = ConnectionConfig.objects.create(
                        protocol=protocol,
                        config_type=existing_connection.config_type,
                        timeout_seconds=existing_connection.timeout_seconds,
                        retry_attempts=existing_connection.retry_attempts,
                        config_data=existing_connection.config_data
                    )

                    # Set the object for get_success_url
                    self.object = new_connection

                    # Return success
                    return HttpResponseRedirect(self.get_success_url())
                else:
                    # Handle missing protocol ID error
                    return self.form_invalid(self.get_form())
            except ConnectionConfig.DoesNotExist:
                # Handle invalid connection ID
                messages.error(request, "The selected connection does not exist.")
                return self.form_invalid(self.get_form())

        # If no existing connection was selected, proceed with normal form processing
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        # Only called when no existing connection was selected
        # Set protocol if it's in the URL
        protocol_id = self.kwargs.get('protocol_id')
        if protocol_id:
            form.instance.protocol = get_object_or_404(TestProtocol, pk=protocol_id)
        else:
            # Handle error - protocol is required
            form.add_error('protocol', 'Protocol is required')
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('testsuite:connection_detail', kwargs={'pk': self.object.pk})


class ConnectionConfigUpdateView(UpdateView):
    model = ConnectionConfig
    template_name = 'test_protocols/connection_form.html'
    fields = ['protocol', 'config_type',
              'timeout_seconds', 'retry_attempts', 'config_data']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        test_protocol = context['object'].protocol
        config_data = context['object'].config_data
        if test_protocol:
            try:
                project = test_protocol.suite.project
                context['environments'] = Environment.objects.filter(project=project)
                # Add existing connections to context
                context['existing_connections'] = ConnectionConfig.objects.filter(
                    protocol__suite=test_protocol.suite
                ).exclude(pk=context['object'].pk)  # Exclude current connection

                if isinstance(config_data, str):
                    value = json.loads(config_data)
                    yaml_string = yaml.dump(value, default_flow_style=False,
                                            indent=2, sort_keys=False)
                    context['object'].config_data = mark_safe(yaml_string)
            except (TestProtocol.DoesNotExist, Environment.DoesNotExist):
                context['environments'] = None
                context['existing_connections'] = ConnectionConfig.objects.none()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Check if using an existing connection
        selected_connection_id = request.POST.get('selected_connection_id')
        if selected_connection_id:
            try:
                # Get the existing connection
                existing_connection = ConnectionConfig.objects.get(pk=selected_connection_id)

                # Update the current connection with values from existing connection
                self.object.config_type = existing_connection.config_type
                self.object.timeout_seconds = existing_connection.timeout_seconds
                self.object.retry_attempts = existing_connection.retry_attempts
                self.object.config_data = existing_connection.config_data
                self.object.save()

                messages.success(request,
                                 "Connection updated successfully using the selected connection's configuration.")
                return HttpResponseRedirect(self.get_success_url())
            except ConnectionConfig.DoesNotExist:
                # Handle invalid connection ID
                messages.error(request, "The selected connection does not exist.")
                return self.form_invalid(self.get_form())

        # If no existing connection was selected, proceed with normal form processing
        return super().post(request, *args, **kwargs)

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

    def get_queryset(self):
        # Use prefetch_related and select_related to efficiently load all related data
        queryset = ProtocolRun.objects.select_related(
            'protocol',  # Load the protocol
            'protocol__suite',  # Load the suite
        ).prefetch_related(
            'protocol__steps',  # Load all execution steps
            'protocol__steps__verification_methods',  # Load verification methods for each step
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all verification results related to this run's protocol's execution steps
        from test_protocols.models import VerificationResult

        # Get all execution steps for this protocol
        execution_steps = self.object.protocol.steps.all()

        # Get all verification methods associated with these steps
        verification_methods = []
        for step in execution_steps:
            verification_methods.extend(step.verification_methods.all())

        # Get verification results for these methods
        verification_results = VerificationResult.objects.filter(
            verification_step__in=verification_methods
        ).select_related('verification_step')

        # Create a dict mapping verification_method_id to result for easy lookup in template
        verification_results_dict = {vr.verification_step_id: vr for vr in verification_results}
        context['verification_results_dict'] = verification_results_dict

        # Add execution steps to context
        context['execution_steps'] = execution_steps

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

    def get(self, request, *args, **kwargs):
        # Check if protocol has a connection config before proceeding
        protocol_id = self.kwargs.get('protocol_id')
        if not protocol_id:
            messages.error(request, "No protocol specified.")
            return redirect('testsuite:protocol_list')

        try:
            protocol = TestProtocol.objects.get(pk=protocol_id)
            # Check if the protocol has a connection config
            try:
                connection_config = protocol.connection_config
            except ConnectionConfig.DoesNotExist:
                messages.error(request,
                               "Unable to run protocol: No connection configuration found. Please add a connection configuration first.")
                return redirect('testsuite:protocol_detail', pk=protocol_id)
        except TestProtocol.DoesNotExist:
            messages.error(request, "Protocol not found.")
            return redirect('testsuite:protocol_list')

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        # Set protocol if it's in the URL
        protocol_id = self.kwargs.get('protocol_id')
        if not protocol_id:
            messages.error(self.request, "No protocol specified.")
            return redirect('testsuite:protocol_list')

        try:
            protocol = TestProtocol.objects.get(pk=protocol_id)

            # Double-check for connection config
            try:
                connection_config = protocol.connection_config
                protocol_run = run_protocol(
                    protocol_id=protocol_id,
                    user=self.request.user,
                    executed_by=form.cleaned_data.get('executed_by')
                )

                # Set self.object so get_success_url works correctly
                self.object = protocol_run

                messages.success(self.request, "Protocol run initiated successfully.")
                return HttpResponseRedirect(self.get_success_url())

            except ConnectionConfig.DoesNotExist:
                messages.error(self.request,
                               "Unable to run protocol: No connection configuration found. Please add a connection configuration first.")
                return redirect('testsuite:protocol_detail', pk=protocol_id)

            form.instance.protocol = protocol
        except TestProtocol.DoesNotExist:
            messages.error(self.request, "Protocol not found.")
            return redirect('testsuite:protocol_list')

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


class RunTestSuiteView(View):
    """View to trigger running all protocols in a test suite"""

    def post(self, request, pk):
        """Handle POST request to run a test suite"""
        try:
            # Run the test suite
            suite = TestSuite.objects.get(pk=pk)
            protocols = suite.get_ordered_protocols()
            if protocols:
                run_suite(pk, request.user)
                messages.success(
                    request,
                    f"Successfully started {len(protocols)} protocols in the test suite."
                )
            else:
                messages.warning(
                    request,
                    "No active protocols found in the test suite."
                )

        except Exception as e:
            # Add an error message
            messages.error(
                request,
                f"Failed to run test suite: {str(e)}"
            )

        # Redirect back to the test suite detail page
        return HttpResponseRedirect(reverse('testsuite:testsuite_detail', kwargs={'pk': pk}))


class ExecutionStepListView(ListView):
    """View for listing all execution steps for a protocol"""
    model = ExecutionStep
    template_name = 'test_protocols/execution_step_list.html'
    context_object_name = 'steps'

    def get_queryset(self):
        self.protocol = get_object_or_404(TestProtocol, pk=self.kwargs['protocol_id'])
        return ExecutionStep.objects.filter(test_protocol=self.protocol)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['protocol'] = self.protocol
        return context


class ExecutionStepCreateView(LoginRequiredMixin, CreateView):
    """View for creating a new execution step"""
    model = ExecutionStep
    template_name = 'test_protocols/execution_step_form.html'
    fields = ['name', 'kwargs']  # This looks correct

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.protocol = get_object_or_404(TestProtocol, pk=self.kwargs['protocol_id'])
        context['test_protocol'] = self.protocol  # Note: make sure this variable matches your template
        context['protocol'] = self.protocol  # Keep both to ensure compatibility
        return context

    def form_valid(self, form):
        form.instance.test_protocol = get_object_or_404(TestProtocol, pk=self.kwargs['protocol_id'])

        # For debugging - print what's coming in through the form
        print(f"Form data: {form.cleaned_data}")
        print(f"Name value: {form.cleaned_data.get('name')}")

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('testsuite:step_list', kwargs={'protocol_id': self.kwargs['protocol_id']})


class ExecutionStepDetailView(DetailView):
    """View for viewing execution step details"""
    model = ExecutionStep
    template_name = 'test_protocols/execution_step_detail.html'
    context_object_name = 'step'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['protocol'] = self.object.test_protocol
        return context


class ExecutionStepUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating an execution step"""
    model = ExecutionStep
    template_name = 'test_protocols/execution_step_form.html'
    fields = ['name','kwargs']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        value = yaml.dump(context['object'].kwargs,
                          default_flow_style=False,
                          indent=2, sort_keys=False
                          )
        context['object'].kwargs = mark_safe(value)

        context['protocol'] = self.object.test_protocol
        return context

    def get_success_url(self):
        return reverse('testsuite:step_detail', kwargs={'pk': self.object.pk})


class ExecutionStepDeleteView(LoginRequiredMixin, DeleteView):
    """View for deleting an execution step"""
    model = ExecutionStep
    template_name = 'test_protocols/execution_step_confirm_delete.html'
    context_object_name = 'step'

    def get_success_url(self):
        return reverse('testsuite:step_list', kwargs={'protocol_id': self.object.test_protocol.id})


class ExecutionStepReorderView(LoginRequiredMixin, View):
    """View for reordering execution steps via AJAX"""

    def post(self, request, protocol_id):
        protocol = get_object_or_404(TestProtocol, pk=protocol_id)

        # Check if protocol is associated with a running test
        active_runs = ProtocolRun.objects.filter(
            protocol=protocol,
            status__in=['started', 'running']
        ).exists()

        if active_runs:
            return JsonResponse({
                'status': 'error',
                'message': 'Cannot reorder steps while protocol is running'
            }, status=400)

        try:
            # Get step ordering data from request
            step_order = request.POST.getlist('steps[]')

            with transaction.atomic():
                # Update order for each step
                for index, step_id in enumerate(step_order):
                    step = get_object_or_404(ExecutionStep, pk=step_id, test_protocol=protocol)
                    # Use 10, 20, 30... for ordering to allow easy insertion later
                    step.order_index = (index + 1) * 10
                    step.save()

            return JsonResponse({'status': 'success'})

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)


class ExecutionStepCloneView(LoginRequiredMixin, View):
    """View for cloning an execution step"""

    def post(self, request, pk):
        original_step = get_object_or_404(ExecutionStep, pk=pk)
        protocol = original_step.test_protocol

        # Check if protocol is associated with a running test
        active_runs = ProtocolRun.objects.filter(
            protocol=protocol,
            status__in=['started', 'running']
        ).exists()

        if active_runs:
            messages.error(request, 'Cannot clone steps while protocol is running')
            return HttpResponseRedirect(reverse('testsuite:step_list',
                                                kwargs={'protocol_id': protocol.id}))

        # Create a clone with a new order_index
        new_step = ExecutionStep.objects.create(
            test_protocol=protocol,
            name=f"Copy of {original_step.name}",
            description=original_step.description,
            args=original_step.args,
            kwargs=original_step.kwargs,
            order_index=original_step.order_index + 5  # Insert after the original
        )

        messages.success(request, f"Successfully cloned step: {original_step.name}")
        return HttpResponseRedirect(reverse('testsuite:step_detail',
                                            kwargs={'pk': new_step.pk}))


class RunExecutionStepsView(LoginRequiredMixin, ListView):
    """View execution steps for a specific protocol run"""
    model = ExecutionStep
    template_name = 'test_protocols/run_execution_steps.html'
    context_object_name = 'steps'

    def get_queryset(self):
        self.run = get_object_or_404(ProtocolRun, pk=self.kwargs['run_id'])
        return ExecutionStep.objects.filter(test_protocol=self.run.protocol).order_by('order_index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['run'] = self.run
        context['protocol'] = self.run.protocol

        # Get the execution status for each step if available
        step_results = {}
        for step in context['steps']:
            # Placeholder - in a real implementation, you would look up step execution results
            # from the database based on the run ID and step ID
            step_results[step.id] = {
                'status': 'not_executed',  # Default status
                'result': None
            }

        context['step_results'] = step_results
        return context


class ExecuteStepView(LoginRequiredMixin, View):
    """Execute a specific step during a protocol run"""

    def post(self, request, run_id, step_id):
        run = get_object_or_404(ProtocolRun, pk=run_id)
        step = get_object_or_404(ExecutionStep, pk=step_id, test_protocol=run.protocol)

        # Only allow execution if run is in the right state
        if run.status not in ['started', 'running']:
            messages.error(request, f"Cannot execute step: run is in {run.status} state")
            return HttpResponseRedirect(reverse('testsuite:run_steps',
                                                kwargs={'run_id': run.id}))

        # Execute the step (placeholder - actual implementation would depend on your execution engine)
        try:
            # In a real implementation, you would:
            # 1. Pass the step to your execution engine
            # 2. Capture the result
            # 3. Store the result in the database
            # 4. Update the run status if needed

            # Simulate success
            messages.success(request, f"Successfully executed step: {step.name}")

        except Exception as e:
            messages.error(request, f"Error executing step: {str(e)}")

        return HttpResponseRedirect(reverse('testsuite:run_steps',
                                            kwargs={'run_id': run.id}))


class ProtocolVerificationListView(ListView):
    model = VerificationMethod
    template_name = 'test_protocols/protocol_verification_list.html'
    context_object_name = 'verifications'

    def get_queryset(self):
        # Filter verification methods for the specific protocol's execution steps
        self.protocol = get_object_or_404(TestProtocol, pk=self.kwargs['protocol_id'])
        return VerificationMethod.objects.filter(execution_step__test_protocol=self.protocol)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['protocol'] = self.protocol
        return context


class ProtocolVerificationDetailView(DetailView):
    model = VerificationMethod
    template_name = 'test_protocols/protocol_verification_detail.html'
    context_object_name = 'verification'

    def get_queryset(self):
        # Ensure the verification method belongs to an execution step of the specified protocol
        self.protocol = get_object_or_404(TestProtocol, pk=self.kwargs['protocol_id'])
        return VerificationMethod.objects.filter(execution_step__test_protocol=self.protocol)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['protocol'] = self.protocol
        context['verification_method_choices'] = dict(VERIFICATION_METHOD_CHOICES)
        context['comparison_operator_choices'] = dict(COMPARISON_OPERATOR_CHOICES)
        return context

class ProtocolVerificationCreateView(CreateView):
    model = VerificationMethod
    template_name = 'test_protocols/protocol_verification_form.html'
    fields = ['name', 'description', 'method_type', 'supports_comparison',
              'comparison_method', 'execution_step', 'config_schema',
              'requires_expected_value', 'supports_dynamic_expected',
              'expected_result']

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Limit execution step choices to those belonging to this protocol
        protocol = get_object_or_404(TestProtocol, pk=self.kwargs['protocol_id'])
        form.fields['execution_step'].queryset = ExecutionStep.objects.filter(test_protocol=protocol)
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.protocol = get_object_or_404(TestProtocol, pk=self.kwargs['protocol_id'])
        context['protocol'] = self.protocol
        context['verification_method_choices'] = VERIFICATION_METHOD_CHOICES
        context['comparison_operator_choices'] = COMPARISON_OPERATOR_CHOICES
        context['is_new'] = True
        return context

    def get_success_url(self):
        return reverse('testsuite:protocol_verification_detail', kwargs={
            'protocol_id': self.kwargs['protocol_id'],
            'pk': self.object.pk
        })


class ProtocolVerificationUpdateView(UpdateView):
    model = VerificationMethod
    template_name = 'test_protocols/protocol_verification_form.html'
    fields = ['name', 'description', 'method_type', 'supports_comparison',
              'comparison_method', 'execution_step', 'config_schema',
              'requires_expected_value', 'supports_dynamic_expected',
              'expected_result']

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Limit execution step choices to those belonging to this protocol
        protocol = get_object_or_404(TestProtocol, pk=self.kwargs['protocol_id'])
        form.fields['execution_step'].queryset = ExecutionStep.objects.filter(test_protocol=protocol)
        return form

    def get_queryset(self):
        # Ensure the verification method belongs to an execution step of the specified protocol
        self.protocol = get_object_or_404(TestProtocol, pk=self.kwargs['protocol_id'])
        return VerificationMethod.objects.filter(execution_step__test_protocol=self.protocol)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['protocol'] = self.protocol
        context['verification_method_choices'] = VERIFICATION_METHOD_CHOICES
        context['comparison_operator_choices'] = COMPARISON_OPERATOR_CHOICES
        context['is_new'] = False
        return context

    def get_success_url(self):
        return reverse('testsuite:protocol_verification_detail', kwargs={
            'protocol_id': self.kwargs['protocol_id'],
            'pk': self.object.pk
        })

class ProtocolVerificationDeleteView(DeleteView):
    model = VerificationMethod
    template_name = 'test_protocols/protocol_verification_confirm_delete.html'
    context_object_name = 'verification'

    def get_queryset(self):
        # Ensure the verification method belongs to an execution step of the specified protocol
        self.protocol = get_object_or_404(TestProtocol, pk=self.kwargs['protocol_id'])
        return VerificationMethod.objects.filter(execution_step__test_protocol=self.protocol)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['protocol'] = self.protocol
        return context

    def get_success_url(self):
        return reverse('testsuite:protocol_verification_list', kwargs={
            'protocol_id': self.kwargs['protocol_id']
        })