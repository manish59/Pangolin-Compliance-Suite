from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import reverse
from .models import Project


class ProjectListView(ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 10  # For pagination

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        return queryset


class ProjectDetailView(DetailView):
    model = Project
    template_name = 'projects/project_detail.html'


class ProjectCreateView(CreateView):
    model = Project
    template_name = 'projects/project_form.html'
    fields = ['name', 'description', 'owner']  # Add relevant fields

    def form_valid(self, form):
        form.instance.owner = self.request.user  # Assign current user as owner

        try:
            # Manually validate the object before saving
            form.instance.clean()
            return super().form_valid(form)
        except ValidationError as e:
            # Add the validation errors to the form
            for field, errors in e.message_dict.items():
                for error in errors:
                    form.add_error(field, error)
            return self.form_invalid(form)
    def get_success_url(self):
        return reverse('project_detail', kwargs={'pk': self.object.pk})


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    template_name = 'projects/project_form.html'  # Can reuse the same template
    fields = ['name', 'description', 'is_active']  # Fields that can be updated

    def get_queryset(self):
        # Ensure users can only update their own projects
        return Project.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        try:
            # Manually validate the object before saving
            form.instance.clean()
            return super().form_valid(form)
        except ValidationError as e:
            # Add the validation errors to the form
            for field, errors in e.message_dict.items():
                for error in errors:
                    form.add_error(field, error)
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('project_detail', kwargs={'pk': self.object.pk})