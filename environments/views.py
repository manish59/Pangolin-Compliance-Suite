# environments/views.py
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    View,
)
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404, render
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseRedirect, FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    View,
)
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.http import HttpResponse

from .models import Environment
from projects.models import Project
from .forms import EnvironmentForm
from .models import Environment
from .forms import EnvironmentForm, EnvironmentToggleForm
from projects.models import Project


class EnvironmentListView(LoginRequiredMixin, ListView):
    model = Environment
    template_name = "environments/environment_list.html"
    context_object_name = "environments"

    def get_queryset(self):
        # Filter environments by projects owned by the current user
        return Environment.objects.filter(project__owner=self.request.user)


class EnvironmentDetailView(LoginRequiredMixin, DetailView):
    model = Environment
    template_name = "environments/environment_detail.html"
    context_object_name = "environment"

    def get_queryset(self):
        # Ensure users can only view their own environments
        return Environment.objects.filter(project__owner=self.request.user)


class EnvironmentCreateView(LoginRequiredMixin, CreateView):
    model = Environment
    form_class = EnvironmentForm
    template_name = "environments/environment_form.html"

    def get_success_url(self):
        # Redirect to the environment list for this project
        return reverse("environments:environment_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add projects owned by the current user to context
        context["projects"] = Project.objects.filter(owner=self.request.user)
        return context

    def form_valid(self, form):
        # Set message for successful creation
        messages.success(
            self.request,
            f"Environment variable '{form.instance.key}' created successfully.",
        )
        return super().form_valid(form)


class EnvironmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Environment
    form_class = EnvironmentForm
    template_name = "environments/environment_form.html"

    def get_success_url(self):
        # Redirect to the environment list for this project
        return reverse("environments:environment_list")

    def get_queryset(self):
        # Ensure users can only update their own environments
        return Environment.objects.filter(project__owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add projects owned by the current user to context
        context["projects"] = Project.objects.filter(owner=self.request.user)
        return context

    def form_valid(self, form):
        # Set message for successful update
        messages.success(
            self.request,
            f"Environment variable '{form.instance.key}' updated successfully.",
        )
        return super().form_valid(form)


class EnvironmentDeleteView(LoginRequiredMixin, DeleteView):
    model = Environment
    template_name = "environments/environment_confirm_delete.html"

    def get_success_url(self):
        # Redirect to the environment list
        return reverse("environments:environment_list")

    def get_queryset(self):
        # Ensure users can only delete their own environments
        return Environment.objects.filter(project__owner=self.request.user)

    def delete(self, request, *args, **kwargs):
        environment = self.get_object()
        messages.success(
            request, f"Environment variable '{environment.key}' deleted successfully."
        )
        return super().delete(request, *args, **kwargs)


class EnvironmentToggleView(LoginRequiredMixin, View):
    """View to toggle the enabled status of an environment variable"""

    def get(self, request, pk):
        environment = get_object_or_404(Environment, pk=pk, project__owner=request.user)
        form = EnvironmentToggleForm()
        return render(
            request,
            "environments/environment_toggle.html",
            {
                "environment": environment,
                "form": form,
            },
        )

    def post(self, request, pk):
        environment = get_object_or_404(Environment, pk=pk, project__owner=request.user)
        form = EnvironmentToggleForm(request.POST)

        if form.is_valid():
            # Toggle the enabled status
            environment.is_enabled = not environment.is_enabled
            environment.save()

            # Set success message
            status = "enabled" if environment.is_enabled else "disabled"
            messages.success(
                request,
                f"Environment variable '{environment.key}' {status} successfully.",
            )

            return redirect("environments:environment_list")

        return render(
            request,
            "environments/environment_toggle.html",
            {
                "environment": environment,
                "form": form,
            },
        )


def download_environment_file(request, pk):
    """View to download a file from a file-type environment variable"""
    env = get_object_or_404(Environment, pk=pk)

    # Check if this is a file type variable
    if env.variable_type != "file" or not env.file_content:
        raise Http404("This environment variable does not contain a downloadable file")

    # Create response with file content
    response = HttpResponse(env.file_content)

    # Set content type if known
    if env.file_type:
        response["Content-Type"] = env.file_type
    else:
        response["Content-Type"] = "application/octet-stream"

    # Set filename in Content-Disposition header
    filename = env.file_name or f"{env.key}_file"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response
