from rest_framework import viewsets
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from api.serializers.profile_serializers import ProfileSerializer

class ProfileViewSet(viewsets.ViewSet):
    """
    API endpoint that allows retrieving profile information by user ID.
    """
    def retrieve(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        serializer = ProfileSerializer(user)
        return Response(serializer.data)
