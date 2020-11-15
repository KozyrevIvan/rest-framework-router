from rest_framework import status, viewsets, mixins, filters
from .serializer import TestModelSerializer
from versioned_router_project.models import TestModel

class TestModelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TestModel.objects.all()
    serializer_class = TestModelSerializer
