���������� Router ��� �������� ��������������� API

{version} ���� r'v[0-9]+'
{api} �������� �������� � api(� ����������� �������� ������������ ��������)

��������� url /{api}/{version}/{application}/{views}/*

����� ��������� ��������� url
/{api}/ - ������ ������ api
/{api}/{version}/ - ������ ���������� application � ������� version 
/{api}/{version}/{application}/ - ������ views � ���������� application � ������ version


��� ���������� ������ ���������� ������� � ���������� �������(�) ��� api ��������:
{application}/{api}/
{application}/{api}/__init__.py
{application}/{api}/router.py - ������ �� �������
{application}/{api}/versioned/{version}/ 
{application}/{api}/versioned/{version}/serializer.py
{application}/{api}/versioned/{version}/views.py
{application}/{api}/versioned/{version}/router.py - ������ �� views


������ ����� {application}/{api}/router.py:
from rest_framework_router.versioned_router_project import ApplicationsDefaultRouter

router = ApplicationsDefaultRouter()
router.register({version})


������ ����� {application}/{api}/versioned/{version}/router.py
from rest_framework_router.versioned_router_project import VersionDefaultRouter
from .views import ExampleViewSet

router = VersionDefaultRouter()
router.register('example', ExampleViewSet)

� �������� urls.py - ������ �� application,api

router = ProjectDefaultRouter('{api}')
router.register('{application}')

urlpatterns = [
    path('{api}/', include(router.urls)),
]

