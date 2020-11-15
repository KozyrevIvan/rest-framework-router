from rest_framework_router.versioned_router_project import ApplicationsDefaultRouter

router = ApplicationsDefaultRouter()
router.register('v1')
router.register('v2')

