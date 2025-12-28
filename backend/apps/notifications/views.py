from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Notification, NotificationSettings, UserPreferences
from .serializers import NotificationSerializer, NotificationSettingsSerializer, UserPreferencesSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user notifications
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return notifications for the current user"""
        return Notification.objects.filter(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        """List all notifications for the current user"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        """Get a single notification"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'status': 'success',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Delete a notification"""
        instance = self.get_object()
        instance.delete()
        return Response({
            'status': 'success',
            'message': 'Notification deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['patch'], url_path='read')
    def mark_as_read(self, request, pk=None):
        """Mark a single notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        serializer = self.get_serializer(notification)
        return Response({
            'status': 'success',
            'message': 'Notification marked as read',
            'data': serializer.data
        })
    
    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_as_read(self, request):
        """Mark all notifications as read for the current user"""
        updated_count = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({
            'status': 'success',
            'message': f'{updated_count} notifications marked as read'
        })
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({
            'status': 'success',
            'data': {'unread_count': count}
        })


class NotificationSettingsViewSet(viewsets.ViewSet):
    """
    ViewSet for managing user notification settings
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get notification settings for the current user"""
        settings, created = NotificationSettings.objects.get_or_create(
            user=request.user
        )
        serializer = NotificationSettingsSerializer(settings)
        return Response({
            'status': 'success',
            'data': serializer.data
        })
    
    def update(self, request):
        """Update notification settings for the current user"""
        settings, created = NotificationSettings.objects.get_or_create(
            user=request.user
        )
        serializer = NotificationSettingsSerializer(
            settings,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'message': 'Settings updated successfully',
                'data': serializer.data
            })
        
        return Response({
            'status': 'error',
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserPreferencesViewSet(viewsets.ViewSet):
    """
    ViewSet for managing user application preferences
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get preferences for the current user"""
        preferences, created = UserPreferences.objects.get_or_create(
            user=request.user
        )
        serializer = UserPreferencesSerializer(preferences)
        return Response({
            'status': 'success',
            'data': serializer.data
        })
    
    def update(self, request):
        """Update preferences for the current user"""
        preferences, created = UserPreferences.objects.get_or_create(
            user=request.user
        )
        serializer = UserPreferencesSerializer(
            preferences,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'message': 'Preferences updated successfully',
                'data': serializer.data
            })
        
        return Response({
            'status': 'error',
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

