Реализация Router для удобного версионирования API

{version} вида r'v[0-9]+'
{api} названия католога с api(в приспективи добавить отображаемое низвание)

Получаемы url /{api}/{version}/{application}/{views}/*

Также поддержка обработки url
/{api}/ - список версий api
/{api}/{version}/ - список приложений application с версией version 
/{api}/{version}/{application}/ - список views в приложении application в версии version


для правильной работы необходимо создать в приложении католог(и) для api например:
{application}/{api}/
{application}/{api}/__init__.py
{application}/{api}/router.py - Роутин по версиям
{application}/{api}/versioned/{version}/ 
{application}/{api}/versioned/{version}/serializer.py
{application}/{api}/versioned/{version}/views.py
{application}/{api}/versioned/{version}/router.py - Роутин по views


Пример файла {application}/{api}/router.py:
from rest_framework_router.versioned_router_project import ApplicationsDefaultRouter

router = ApplicationsDefaultRouter()
router.register({version})


Пример файла {application}/{api}/versioned/{version}/router.py
from rest_framework_router.versioned_router_project import VersionDefaultRouter
from .views import ExampleViewSet

router = VersionDefaultRouter()
router.register('example', ExampleViewSet)

в основном urls.py - Роутин по application,api

router = ProjectDefaultRouter('{api}')
router.register('{application}')

urlpatterns = [
    path('{api}/', include(router.urls)),
]

