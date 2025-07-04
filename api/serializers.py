from django.utils import timezone
from datetime import datetime
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from user.models import CustomUser
from courses.models import Course


class CourseSerializer(serializers.ModelSerializer):
    time_since_creation = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = '__all__'

    def get_time_since_creation(self, obj):
        delta = timezone.now() - obj.created_at
        days = delta.days
        months = days // 30
        years = days // 365
        return {'days': days, 'months': months, 'years': years}


class SignupSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'profile_image']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }

    def create(self, validated_data):
        profile_image = validated_data.pop('profile_image', None)
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        if profile_image:
            user.profile_image = profile_image
            user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data.update({
            'username': self.user.username,
            'email': self.user.email,
            'profile_image': str(self.user.profile_image) if self.user.profile_image else None,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'is_staff': self.user.is_staff,
        })
        return data
