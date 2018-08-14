from __future__ import unicode_literals

import pytest
from django.test import TestCase

from rest_framework import status
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import (
    action, api_view, authentication_classes, detail_route, list_route,
    parser_classes, permission_classes, renderer_classes, schema,
    throttle_classes
)
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
from rest_framework.test import APIRequestFactory
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView


class DecoratorTestCase(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()

    def _finalize_response(self, request, response, *args, **kwargs):
        response.request = request
        return APIView.finalize_response(self, request, response, *args, **kwargs)

    def test_api_view_incorrect(self):
        """
        If @api_view is not applied correct, we should raise an assertion.
        """

        @api_view
        def view(request):
            return Response()

        request = self.factory.get('/')
        self.assertRaises(AssertionError, view, request)

    def test_api_view_incorrect_arguments(self):
        """
        If @api_view is missing arguments, we should raise an assertion.
        """

        with self.assertRaises(AssertionError):
            @api_view('GET')
            def view(request):
                return Response()

    def test_calling_method(self):

        @api_view(['GET'])
        def view(request):
            return Response({})

        request = self.factory.get('/')
        response = view(request)
        assert response.status_code == status.HTTP_200_OK

        request = self.factory.post('/')
        response = view(request)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_calling_put_method(self):

        @api_view(['GET', 'PUT'])
        def view(request):
            return Response({})

        request = self.factory.put('/')
        response = view(request)
        assert response.status_code == status.HTTP_200_OK

        request = self.factory.post('/')
        response = view(request)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_calling_patch_method(self):

        @api_view(['GET', 'PATCH'])
        def view(request):
            return Response({})

        request = self.factory.patch('/')
        response = view(request)
        assert response.status_code == status.HTTP_200_OK

        request = self.factory.post('/')
        response = view(request)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_renderer_classes(self):

        @api_view(['GET'])
        @renderer_classes([JSONRenderer])
        def view(request):
            return Response({})

        request = self.factory.get('/')
        response = view(request)
        assert isinstance(response.accepted_renderer, JSONRenderer)

    def test_parser_classes(self):

        @api_view(['GET'])
        @parser_classes([JSONParser])
        def view(request):
            assert len(request.parsers) == 1
            assert isinstance(request.parsers[0], JSONParser)
            return Response({})

        request = self.factory.get('/')
        view(request)

    def test_authentication_classes(self):

        @api_view(['GET'])
        @authentication_classes([BasicAuthentication])
        def view(request):
            assert len(request.authenticators) == 1
            assert isinstance(request.authenticators[0], BasicAuthentication)
            return Response({})

        request = self.factory.get('/')
        view(request)

    def test_permission_classes(self):

        @api_view(['GET'])
        @permission_classes([IsAuthenticated])
        def view(request):
            return Response({})

        request = self.factory.get('/')
        response = view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_throttle_classes(self):
        class OncePerDayUserThrottle(UserRateThrottle):
            rate = '1/day'

        @api_view(['GET'])
        @throttle_classes([OncePerDayUserThrottle])
        def view(request):
            return Response({})

        request = self.factory.get('/')
        response = view(request)
        assert response.status_code == status.HTTP_200_OK

        response = view(request)
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_schema(self):
        """
        Checks CustomSchema class is set on view
        """
        class CustomSchema(AutoSchema):
            pass

        @api_view(['GET'])
        @schema(CustomSchema())
        def view(request):
            return Response({})

        assert isinstance(view.cls.schema, CustomSchema)


class ActionDecoratorTestCase(TestCase):

    def test_defaults(self):
        @action(detail=True)
        def test_action(request):
            pass

        assert test_action.bind_to_methods == ['get']
        assert test_action.detail is True
        assert test_action.url_path == 'test_action'
        assert test_action.url_name == 'test-action'

    def test_detail_required(self):
        with pytest.raises(AssertionError) as excinfo:
            @action()
            def test_action(request):
                pass

        assert str(excinfo.value) == "@action() missing required argument: 'detail'"

    def test_detail_route_deprecation(self):
        with pytest.warns(PendingDeprecationWarning) as record:
            @detail_route()
            def view(request):
                pass

        assert len(record) == 1
        assert str(record[0].message) == (
            "`detail_route` is pending deprecation and will be removed in "
            "3.10 in favor of `action`, which accepts a `detail` bool. Use "
            "`@action(detail=True)` instead."
        )

    def test_list_route_deprecation(self):
        with pytest.warns(PendingDeprecationWarning) as record:
            @list_route()
            def view(request):
                pass

        assert len(record) == 1
        assert str(record[0].message) == (
            "`list_route` is pending deprecation and will be removed in "
            "3.10 in favor of `action`, which accepts a `detail` bool. Use "
            "`@action(detail=False)` instead."
        )

    def test_route_url_name_from_path(self):
        # pre-3.8 behavior was to base the `url_name` off of the `url_path`
        with pytest.warns(PendingDeprecationWarning):
            @list_route(url_path='foo_bar')
            def view(request):
                pass

        assert view.url_path == 'foo_bar'
        assert view.url_name == 'foo-bar'