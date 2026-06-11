"""Activities序列化器"""
from rest_framework import serializers
from .models import Activity, ActivityEnrollment


class ActivitySerializer(serializers.ModelSerializer):
    organizer = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = ['uuid', 'title', 'description', 'cover_url', 'activity_type',
                  'host_school', 'location', 'start_time', 'end_time',
                  'max_attendees', 'current_attendees', 'enrollment_mode',
                  'fee', 'status', 'organizer']

    def get_organizer(self, obj):
        if hasattr(obj, 'organizer') and obj.organizer:
            return {
                'real_name': obj.organizer.real_name,
                'company': obj.organizer.company,
                'avatar_url': obj.organizer.user.avatar_url if hasattr(obj.organizer, 'user') else '',
            }
        return None


class ActivityEnrollmentSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = ActivityEnrollment
        fields = ['profile', 'enrollment_status', 'ai_recommended', 'ai_match_score']

    def get_profile(self, obj):
        return {
            'uuid': str(obj.profile.uuid),
            'real_name': obj.profile.real_name,
            'company': obj.profile.company,
            'position': obj.profile.position,
            'cert_level': obj.profile.cert_level,
            'avatar_url': obj.profile.user.avatar_url,
        }
