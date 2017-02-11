from __future__ import absolute_import, unicode_literals

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from rest_framework import generics

from acls.models import AccessControlList
from permissions import Permission
from rest_api.filters import MayanObjectPermissionsFilter
from rest_api.permissions import MayanPermission

from .models import SmartLink
from .permissions import (
    permission_smart_link_create, permission_smart_link_delete,
    permission_smart_link_edit, permission_smart_link_view
)
from .serializers import SmartLinkConditionSerializer, SmartLinkSerializer


class APISmartLinkConditionListView(generics.ListCreateAPIView):
    serializer_class = SmartLinkConditionSerializer

    def get(self, *args, **kwargs):
        """
        Returns a list of all the smart link conditions.
        """
        return super(APISmartLinkConditionListView, self).get(*args, **kwargs)

    def get_queryset(self):
        return self.get_smart_link().conditions.all()

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {
            'format': self.format_kwarg,
            'request': self.request,
            'smart_link': self.get_smart_link(),
            'view': self
        }

    def get_smart_link(self):
        if self.request.method == 'GET':
            permission_required = permission_smart_link_view
        else:
            permission_required = permission_smart_link_edit

        smart_link = get_object_or_404(SmartLink, pk=self.kwargs['pk'])

        try:
            Permission.check_permissions(
                self.request.user, (permission_required,)
            )
        except PermissionDenied:
            AccessControlList.objects.check_access(
                permission_required, self.request.user, smart_link
            )

        return smart_link

    def post(self, *args, **kwargs):
        """
        Create a new smart link condition.
        """
        return super(APISmartLinkConditionListView, self).post(*args, **kwargs)


class APISmartLinkConditionView(generics.RetrieveUpdateDestroyAPIView):
    lookup_url_kwarg = 'condition_pk'
    serializer_class = SmartLinkConditionSerializer

    def delete(self, *args, **kwargs):
        """
        Delete the selected smart link condition.
        """

        return super(APISmartLinkConditionView, self).delete(*args, **kwargs)

    def get(self, *args, **kwargs):
        """
        Return the details of the selected smart link condition.
        """

        return super(APISmartLinkConditionView, self).get(*args, **kwargs)

    def get_queryset(self):
        return self.get_smart_link().conditions.all()

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {
            'format': self.format_kwarg,
            'request': self.request,
            'smart_link': self.get_smart_link(),
            'view': self
        }

    def get_smart_link(self):
        if self.request.method == 'GET':
            permission_required = permission_smart_link_view
        else:
            permission_required = permission_smart_link_edit

        smart_link = get_object_or_404(SmartLink, pk=self.kwargs['pk'])

        try:
            Permission.check_permissions(
                self.request.user, (permission_required,)
            )
        except PermissionDenied:
            AccessControlList.objects.check_access(
                permission_required, self.request.user, smart_link
            )

        return smart_link

    def patch(self, *args, **kwargs):
        """
        Edit the selected smart link condition.
        """

        return super(APISmartLinkConditionView, self).patch(*args, **kwargs)

    def put(self, *args, **kwargs):
        """
        Edit the selected smart link condition.
        """

        return super(APISmartLinkConditionView, self).put(*args, **kwargs)


class APISmartLinkListView(generics.ListCreateAPIView):
    filter_backends = (MayanObjectPermissionsFilter,)
    mayan_object_permissions = {'GET': (permission_smart_link_view,)}
    mayan_view_permissions = {'POST': (permission_smart_link_create,)}
    permission_classes = (MayanPermission,)
    queryset = SmartLink.objects.all()
    serializer_class = SmartLinkSerializer

    def get(self, *args, **kwargs):
        """
        Returns a list of all the smart links.
        """

        return super(APISmartLinkListView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        """
        Create a new smart link.
        """

        return super(APISmartLinkListView, self).post(*args, **kwargs)


class APISmartLinkView(generics.RetrieveUpdateDestroyAPIView):
    filter_backends = (MayanObjectPermissionsFilter,)
    mayan_object_permissions = {
        'DELETE': (permission_smart_link_delete,),
        'GET': (permission_smart_link_view,),
        'PATCH': (permission_smart_link_edit,),
        'PUT': (permission_smart_link_edit,)
    }
    queryset = SmartLink.objects.all()
    serializer_class = SmartLinkSerializer

    def delete(self, *args, **kwargs):
        """
        Delete the selected smart link.
        """

        return super(APISmartLinkView, self).delete(*args, **kwargs)

    def get(self, *args, **kwargs):
        """
        Return the details of the selected smart ink.
        """

        return super(APISmartLinkView, self).get(*args, **kwargs)

    def patch(self, *args, **kwargs):
        """
        Edit the selected smart link.
        """

        return super(APISmartLinkView, self).patch(*args, **kwargs)

    def put(self, *args, **kwargs):
        """
        Edit the selected smart link.
        """

        return super(APISmartLinkView, self).put(*args, **kwargs)
