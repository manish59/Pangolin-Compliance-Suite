from rest_framework import serializers
from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    """
    Serializer for the Project model.
    """
    owner_username = serializers.ReadOnlyField(source='owner.username')
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'owner', 'owner_username', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['owner', 'created_at', 'updated_at']

    def validate_name(self, value):
        """
        Validate project name.
        """
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Project name must be at least 3 characters.")
        return value

    def validate(self, data):
        """
        Validate that the project name is unique for this user.
        """
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            name = data.get('name')

            # Check for existing projects with the same name for this user
            queryset = Project.objects.filter(name__iexact=name, owner=user)

            # If this is an update, exclude the current instance
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise serializers.ValidationError({'name': "You already have a project with this name."})

        return data

    def create(self, validated_data):
        """
        Create and return a new Project instance.
        """
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['owner'] = request.user
        return super().create(validated_data)