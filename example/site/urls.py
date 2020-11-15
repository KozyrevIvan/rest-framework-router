from django.contrib import admin
from django.urls import path, include

from  rest_framework_router.versioned_router_project  import ProjectDefaultRouter


router = ProjectDefaultRouter('api_web')
router.register('versioned_router_project')


urlpatterns = [
    path('api_web/', include(router.urls)),
]
