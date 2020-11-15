import itertools
from collections import OrderedDict, namedtuple

from django.core.exceptions import ImproperlyConfigured
from django.urls import NoReverseMatch, re_path

import importlib
from rest_framework import views
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.schemas import SchemaGenerator
from rest_framework.schemas.views import SchemaView
from rest_framework.settings import api_settings
from rest_framework.urlpatterns import format_suffix_patterns

Route = namedtuple('Route', ['url', 'mapping', 'name', 'detail', 'initkwargs'])
DynamicRoute = namedtuple('DynamicRoute', ['url', 'name', 'detail', 'initkwargs'])


def escape_curly_brackets(url_path):
    """
    Double brackets in regex of url_path for escape string formatting
    """
    return url_path.replace('{', '{{').replace('}', '}}')


def flatten(list_of_lists):
    """
    Takes an iterable of iterables, returns a single iterable containing all items
    """
    return itertools.chain(*list_of_lists)


class APIVersionedView(views.APIView):
    """
    The default basic root view for DefaultRouter
    """
    _ignore_model_permissions = True
    schema = None  # exclude from schema
    api_versioned_dict = None

    def get(self, request, versioned, *args, **kwargs):
        # Return a plain {"name": "hyperlink"} response.
        ret = OrderedDict()
        namespace = request.resolver_match.namespace
        for key, url_name in self.api_versioned_dict[versioned].items():
            if namespace:
                url_name = namespace + ':' + url_name
            try:
                kwargs["versioned"]=versioned
                kwargs["application"]=key
                ret[key] = reverse(
                    url_name,
                    args=args,
                    kwargs=kwargs,
                    request=request,
                    format=kwargs.get('format', None)
                )
            except NoReverseMatch:
                # Don't bail out if eg. no list routes exist, only detail routes.
                continue

        return Response(ret)


class APIApplicationView(views.APIView):
    """
    The default basic root view for DefaultRouter
    """
    _ignore_model_permissions = True
    schema = None  # exclude from schema
    api_application_dict = None

    def get(self, request,versioned,application, *args, **kwargs):
        # Return a plain {"name": "hyperlink"} response.
        ret = OrderedDict()
        namespace = request.resolver_match.namespace
        for key, url_name in self.api_application_dict[versioned][application].items():
            if namespace:
                url_name = namespace + ':' + url_name
            try:
                print(url_name,kwargs)
                ret[key] = reverse(
                    url_name,
                    args=args,
                    kwargs=kwargs,
                    request=request,
                    format=kwargs.get('format', None)
                )
            except NoReverseMatch:
                # Don't bail out if eg. no list routes exist, only detail routes.
                continue

        return Response(ret)


class APIRootView(views.APIView):
    """
    The default basic root view for DefaultRouter
    """
    _ignore_model_permissions = True
    schema = None  # exclude from schema
    api_root_dict = None

    def get(self, request,*args, **kwargs):
        # Return a plain {"name": "hyperlink"} response.
        ret = OrderedDict()
        namespace = request.resolver_match.namespace
        for key, url_name in self.api_root_dict.items():
            if namespace:
                url_name = namespace + ':' + url_name
            try:
                kwargs["versioned"]=key
                ret[key] = reverse(
                    url_name,
                    args=args,
                    kwargs=kwargs,
                    request=request,
                    format=kwargs.get('format', None)
                )
            except NoReverseMatch:
                # Don't bail out if eg. no list routes exist, only detail routes.
                continue
        
        return Response(ret)


class BaseRouter:
    def __init__(self, api_name="api"):
        self.registry = []
        self.api_name = api_name

    def register(self, application):
        self.registry.append(application)

        if hasattr(self, '_urls'):
            del self._urls
    

    def get_urls(self):
        """
        Return a list of URL patterns, given the registered viewsets.
        """
        raise NotImplementedError('get_urls must be overridden')

    @property
    def urls(self):
        if not hasattr(self, '_urls'):
            self._urls = self.get_urls()
        return self._urls
  

class SimpleRouter(BaseRouter):

    routes = [
        # List route.
        Route(
            url=r'^{versioned}/{application}/{prefix}{trailing_slash}$',
            mapping={
                'get': 'list',
                'post': 'create'
            },
            name='{application}-{basename}-{versioned}-list',
            detail=False,
            initkwargs={'suffix': 'List'}
        ),
        # Dynamically generated list routes. Generated using
        # @action(detail=False) decorator on methods of the viewset.
        DynamicRoute(
            url=r'^{versioned}/{application}/{prefix}/{url_path}{trailing_slash}$',
            name='{application}-{basename}-{versioned}-{url_name}',
            detail=False,
            initkwargs={}
        ),
        # Detail route.
        Route(
            url=r'^{versioned}/{application}/{prefix}/{lookup}{trailing_slash}$',
            mapping={
                'get': 'retrieve',
                'put': 'update',
                'patch': 'partial_update',
                'delete': 'destroy'
            },
            name='{application}-{basename}-{versioned}-detail',
            detail=True,
            initkwargs={'suffix': 'Instance'}
        ),
        # Dynamically generated detail routes. Generated using
        # @action(detail=True) decorator on methods of the viewset.
        DynamicRoute(
            url=r'^{versioned}/{application}/{prefix}/{lookup}/{url_path}{trailing_slash}$',
            name='{application}-{basename}-{versioned}-{url_name}',
            detail=True,
            initkwargs={}
        ),
    ]

    def __init__(self, api_name="api", trailing_slash=True):
        self.trailing_slash = '/' if trailing_slash else ''
        super().__init__(api_name)

    def get_name_versioned_router(self,applications,package,version):
        return f"{applications}.{self.api_name}.{package}.{version}.router"

    def get_name_applications_router(self,applications):
        return f"{applications}.{self.api_name}.router"

    def get_routes(self, viewset):
        """
        Augment `self.routes` with any dynamically generated routes.

        Returns a list of the Route namedtuple.
        """
        # converting to list as iterables are good for one pass, known host needs to be checked again and again for
        # different functions.
        known_actions = list(flatten([route.mapping.values() for route in self.routes if isinstance(route, Route)]))
        extra_actions = viewset.get_extra_actions()

        # checking action names against the known actions list
        not_allowed = [
            action.__name__ for action in extra_actions
            if action.__name__ in known_actions
        ]
        if not_allowed:
            msg = ('Cannot use the @action decorator on the following '
                   'methods, as they are existing routes: %s')
            raise ImproperlyConfigured(msg % ', '.join(not_allowed))

        # partition detail and list actions
        detail_actions = [action for action in extra_actions if action.detail]
        list_actions = [action for action in extra_actions if not action.detail]

        routes = []
        for route in self.routes:
            if isinstance(route, DynamicRoute) and route.detail:
                routes += [self._get_dynamic_route(route, action) for action in detail_actions]
            elif isinstance(route, DynamicRoute) and not route.detail:
                routes += [self._get_dynamic_route(route, action) for action in list_actions]
            else:
                routes.append(route)

        return routes

    def _get_dynamic_route(self, route, action):
        initkwargs = route.initkwargs.copy()
        initkwargs.update(action.kwargs)

        url_path = escape_curly_brackets(action.url_path)

        return Route(
            url=route.url.replace('{url_path}', url_path),
            mapping=action.mapping,
            name=route.name.replace('{url_name}', action.url_name),
            detail=route.detail,
            initkwargs=initkwargs,
        )

    def get_method_map(self, viewset, method_map):
        """
        Given a viewset, and a mapping of http methods to actions,
        return a new mapping which only includes any mappings that
        are actually implemented by the viewset.
        """
        bound_methods = {}
        for method, action in method_map.items():
            if hasattr(viewset, action):
                bound_methods[method] = action
        return bound_methods

    def get_lookup_regex(self, viewset, lookup_prefix=''):
        """
        Given a viewset, return the portion of URL regex that is used
        to match against a single instance.

        Note that lookup_prefix is not used directly inside REST rest_framework
        itself, but is required in order to nicely support nested router
        implementations, such as drf-nested-routers.

        https://github.com/alanjds/drf-nested-routers
        """
        base_regex = '(?P<{lookup_prefix}{lookup_url_kwarg}>{lookup_value})'
        # Use `pk` as default field, unset set.  Default regex should not
        # consume `.json` style suffixes and should break at '/' boundaries.
        lookup_field = getattr(viewset, 'lookup_field', 'pk')
        lookup_url_kwarg = getattr(viewset, 'lookup_url_kwarg', None) or lookup_field
        lookup_value = getattr(viewset, 'lookup_value_regex', '[^/.]+')
        return base_regex.format(
            lookup_prefix=lookup_prefix,
            lookup_url_kwarg=lookup_url_kwarg,
            lookup_value=lookup_value
        )

    def get_urls(self):
        ret = []
        for application in self.registry:
            router = importlib.import_module(self.get_name_applications_router(application))
            for application_ret in self.get_urls_application(application,router):
                ret.append(application_ret)

        return ret

    def get_urls_application(self,application,application_router):
        ret = []
        for version,package in application_router.router.registry:
            router = importlib.import_module(self.get_name_versioned_router(application,package,version))
            for versioned_ret in self.get_urls_versioned(application,version,router):
                ret.append(versioned_ret)
        return ret

    def get_urls_versioned(self,application,versioned,versioned_router):
        """
        Use the registered viewsets to generate a list of URL patterns.
        """
        ret = []

        for prefix, viewset, basename in versioned_router.router.registry:
            lookup = self.get_lookup_regex(viewset)
            routes = self.get_routes(viewset)

            for route in routes:

                # Only actions which actually exist on the viewset will be bound
                mapping = self.get_method_map(viewset, route.mapping)
                if not mapping:
                    continue

                # Build the url pattern
                regex = route.url.format(
                    prefix=prefix,
                    lookup=lookup,
                    application=application,
                    versioned=versioned,
                    trailing_slash=self.trailing_slash
                )

                if not prefix and regex[:2] == '^/':
                    regex = '^' + regex[2:]

                initkwargs = route.initkwargs.copy()
                initkwargs.update({
                    'basename': basename,
                    'detail': route.detail,
                })

                view = viewset.as_view(mapping, **initkwargs)
                name = route.name.format(basename=basename,versioned=versioned,application=application)
                ret.append(re_path(regex, view, name=name))

        return ret


class ProjectDefaultRouter(SimpleRouter):
    """
    The default router extends the SimpleRouter, but also adds in a default
    API root view, and adds format suffix patterns to the URLs.
    """
    include_root_view = True
    include_versioned_view = True
    include_application_view = True

    include_format_suffixes = True

    root_view_name = 'api-root'
    versioned_view_name = 'api-versioned'
    applications_view_name = 'api-applications'

    default_schema_renderers = None

    APIRootView = APIRootView
    APIVersionedView = APIVersionedView
    APIApplicationView = APIApplicationView

    APISchemaView = SchemaView
    SchemaGenerator = SchemaGenerator

    def __init__(self, *args, **kwargs):
        if 'root_renderers' in kwargs:
            self.root_renderers = kwargs.pop('root_renderers')
        else:
            self.root_renderers = list(api_settings.DEFAULT_RENDERER_CLASSES)
        super().__init__(*args, **kwargs)

    def get_api_root_view(self,api_urls=None):
        """
        Return a basic root view.
        """
        api_root_dict = OrderedDict()
        for application in self.registry:
            applications_router = importlib.import_module(self.get_name_applications_router(application))
            for versioned,package in applications_router.router.registry:
                api_root_dict[versioned] = self.versioned_view_name

        return self.APIRootView.as_view(api_root_dict=api_root_dict)

    def get_api_versioned_view(self, api_urls=None):
        """
        Return a basic root view.
        """
        api_versioned_dict = OrderedDict()
        for application in self.registry:
            applications_router = importlib.import_module(self.get_name_applications_router(application))
            for versioned,package in applications_router.router.registry:
                if not versioned in api_versioned_dict:
                    api_versioned_dict[versioned] = OrderedDict()
                api_versioned_dict[versioned][application]= self.applications_view_name

        return self.APIVersionedView.as_view(api_versioned_dict=api_versioned_dict)

    def get_api_application_view(self,api_urls=None):
        """
        Return a basic root view.
        """
        api_application_dict = OrderedDict()
        list_name = self.routes[0].name
        for application in self.registry:
            applications_router = importlib.import_module(self.get_name_applications_router(application))

            for versioned,package in applications_router.router.registry:
                if not versioned in api_application_dict:
                    api_application_dict[versioned] = OrderedDict()
                if not application in api_application_dict[versioned]:
                    api_application_dict[versioned][application] = OrderedDict()

                versioned_router = importlib.import_module(self.get_name_versioned_router(application,package,versioned))
                for prefix, viewset, basename in versioned_router.router.registry:
                    api_application_dict[versioned][application][prefix] = list_name.format(basename=basename,versioned=versioned,application=application)
        print(api_application_dict)

        return self.APIApplicationView.as_view(api_application_dict=api_application_dict)

    def get_urls(self):
        """
        Generate the list of URL patterns, including a default root view
        for the API, and appending `.json` style format suffixes.
        """
        urls = super().get_urls()

        if self.include_root_view:
            view = self.get_api_root_view(api_urls=urls)
            root_url = re_path(r'^$', view, name=self.root_view_name)
            urls.append(root_url)

        if self.include_versioned_view:
            view = self.get_api_versioned_view(api_urls=urls)
            versioned_url = re_path(r'^(?P<versioned>v[0-9]+)/$', view, name=self.versioned_view_name)
            urls.append(versioned_url)
  
        if self.include_application_view:
            view = self.get_api_application_view(api_urls=urls)
            application_url = re_path(r'^(?P<versioned>v[0-9]+)/(?P<application>[A-z0-9]+)/$', view, name=self.applications_view_name)
            urls.append(application_url)





        if self.include_format_suffixes:
            urls = format_suffix_patterns(urls)
        
        return urls


class VersionDefaultRouter:
    def __init__(self):
        self.registry = []

    def register(self, prefix, viewset, basename=None):
        if basename is None:
            basename = self.get_default_basename(viewset)
        self.registry.append((prefix, viewset, basename))

    def get_default_basename(self, viewset):
        """
        If `basename` is not specified, attempt to automatically determine
        it from the viewset.
        """
        queryset = getattr(viewset, 'queryset', None)

        assert queryset is not None, '`basename` argument not specified, and could ' \
            'not automatically determine the name from the viewset, as ' \
            'it does not have a `.queryset` attribute.'

        return queryset.model._meta.object_name.lower()


class ApplicationsDefaultRouter:
    def __init__(self):
        self.registry = []

    def register(self, version, package='versioned'):
        self.registry.append((version,package))
