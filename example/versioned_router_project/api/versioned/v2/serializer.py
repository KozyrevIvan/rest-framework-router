from rest_framework import serializers
from versioned_router_project.models import TestModel


class TestModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestModel
        fields = ('id', 'name', 'description')
        