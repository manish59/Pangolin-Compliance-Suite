# environments/views.py
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Environment
from projects.models import Project

class EnvironmentListView(ListView):
    model = Environment
    template_name = 'environments/environment_list.html'
    context_object_name = 'environments'

class EnvironmentDetailView(DetailView):
    model = Environment
    template_name = 'environments/environment_detail.html'
    context_object_name = 'environment'

class EnvironmentCreateView(CreateView):

    model = Environment
    template_name = 'environments/environment_form.html'
    fields = ['project', 'key', 'value', 'variable_type', 'description', 'is_enabled']
    success_url = reverse_lazy('environments:environment_list')

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context['projects'] = Project.objects.filter(owner=self.request.user)
        return context

class EnvironmentUpdateView(UpdateView):
    model = Environment
    template_name = 'environments/environment_form.html'
    fields = ['project', 'key', 'value', 'variable_type', 'description', 'is_enabled']
    success_url = reverse_lazy('environments:environment_list')
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context['projects'] = Project.objects.filter(owner=self.request.user)
        return context

class EnvironmentDeleteView(DeleteView):
    model = Environment
    template_name = 'environments/environment_confirm_delete.html'
    success_url = reverse_lazy('environments:environment_list')