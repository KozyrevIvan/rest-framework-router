from rest_framework_router.versioned_router_project import VersionDefaultRouter
from .views import TestModelViewSet

router = VersionDefaultRouter()
router.register(r'test_model', TestModelViewSet)