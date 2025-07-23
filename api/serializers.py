import requests
import cloudinary.uploader
from django.utils import timezone
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.db.models import Sum
from rest_framework_simplejwt.tokens import RefreshToken
from user.models import CustomUser, UserLesson, UserCourse
from courses.models import (
    Course, Lesson, Component, Video, Text, MultipleChoiceQuestion, MultipleOptionsQuestion, CodingQuestion,
    MultipleChoiceOption, MultipleOptionsOption, CodingTest, Certificate
)


class UserCourseSerializer(serializers.ModelSerializer):
    course = serializers.StringRelatedField()

    class Meta:
        model = UserCourse
        fields = '__all__'


class CourseSerializer(serializers.ModelSerializer):
    time_since_creation = serializers.SerializerMethodField()
    total_score = serializers.SerializerMethodField()
    user_courses = UserCourseSerializer(source='usercourse_set', many=True, read_only=True)

    class Meta:
        model = Course
        fields = '__all__'

    def get_time_since_creation(self, obj):
        delta = timezone.now() - obj.created_at
        days = delta.days
        months = days // 30
        years = days // 365
        return {'days': days, 'months': months, 'years': years}

    def get_total_score(self, obj):
        return obj.lessons.aggregate(total=Sum('max_score'))['total'] or 0


class UserLessonSerializer(serializers.ModelSerializer):
    lesson = serializers.StringRelatedField()

    class Meta:
        model = UserLesson
        fields = '__all__'


# questions data serializers
class MultipleChoiceOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MultipleChoiceOption
        fields = '__all__'


class MultipleOptionsOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MultipleOptionsOption
        fields = '__all__'


class CodingTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodingTest
        fields = '__all__'


# Serializers for child models
class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ('video_url',)  # Specific fields only


class TextSerializer(serializers.ModelSerializer):
    class Meta:
        model = Text
        fields = ('content',)


class MultipleChoiceQuestionSerializer(serializers.ModelSerializer):
    options = MultipleChoiceOptionSerializer(many=True, read_only=True)

    class Meta:
        model = MultipleChoiceQuestion
        fields = ('question', 'options')


class MultipleOptionsQuestionSerializer(serializers.ModelSerializer):
    options = MultipleOptionsOptionSerializer(many=True, read_only=True)

    class Meta:
        model = MultipleOptionsQuestion
        fields = ('question', 'options')


class CodingQuestionSerializer(serializers.ModelSerializer):
    tests = CodingTestSerializer(many=True, read_only=True)

    class Meta:
        model = CodingQuestion
        fields = '__all__'


# Component Serializer with custom logic
class ComponentSerializer(serializers.ModelSerializer):
    data = serializers.SerializerMethodField()

    class Meta:
        model = Component
        fields = ('id', 'lesson', 'type', 'max_score', 'serial_number', 'data')

    def get_data(self, obj):
        type_map = {
            'video': Video,
            'text': Text,
            'mcq': MultipleChoiceQuestion,
            'moq': MultipleOptionsQuestion,
            'coding': CodingQuestion,
        }
        child_model = type_map.get(obj.type)
        if child_model:
            try:
                child_instance = child_model.objects.get(id=obj.id)
                if isinstance(child_instance, Video):
                    return VideoSerializer(child_instance).data
                elif isinstance(child_instance, Text):
                    return TextSerializer(child_instance).data
                elif isinstance(child_instance, MultipleChoiceQuestion):
                    return MultipleChoiceQuestionSerializer(child_instance).data
                elif isinstance(child_instance, MultipleOptionsQuestion):
                    return MultipleOptionsQuestionSerializer(child_instance).data
                elif isinstance(child_instance, CodingQuestion):
                    return CodingQuestionSerializer(child_instance).data
            except child_model.DoesNotExist:
                return {}
        return {}


# Lesson Serializer
class LessonSerializer(serializers.ModelSerializer):
    user_lessons = UserLessonSerializer(source='userlesson_set', many=True, read_only=True)
    components = ComponentSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = '__all__'


class CustomUserWithLessonsSerializer(serializers.ModelSerializer):
    user_lessons = UserLessonSerializer(source='userlesson_set', many=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'user_lessons']


class CertificateSerializer(serializers.ModelSerializer):
    student = serializers.StringRelatedField(read_only=True)
    course = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Certificate
        fields = '__all__'


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
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'profile_image': str(self.user.profile_image) if self.user.profile_image else None,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'is_staff': self.user.is_staff,
        })
        return data


class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField(required=True)
    provider = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs.get('provider') != 'google':
            raise serializers.ValidationError({'provider': 'Provider must be "google"'})

        id_token = attrs.get('id_token')
        try:
            # Verify Google ID token
            response = requests.get(f'https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={id_token}')
            if response.status_code != 200:
                raise serializers.ValidationError({'id_token': 'Invalid Google ID token'})
            google_data = response.json()
            email = google_data.get('email')
            if not email:
                raise serializers.ValidationError({'email': 'Email not provided by Google'})
            attrs['google_data'] = google_data
        except Exception as e:
            raise serializers.ValidationError({'id_token': f'Error verifying token: {str(e)}'})
        return attrs

    def create(self, validated_data):
        google_data = validated_data['google_data']
        email = google_data['email']
        first_name = google_data.get('given_name', '')
        last_name = google_data.get('family_name', '')
        username = email[:email.index('@')]

        # Check if user exists
        try:
            user = CustomUser.objects.get(email=email)
            is_new_user = False
        except CustomUser.DoesNotExist:
            # Create new user
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=None  # No password for Google users
            )
            # Optionally fetch profile image
            if google_data.get('picture'):
                response = requests.get(google_data['picture'])
                if response.status_code == 200:
                    upload_result = cloudinary.uploader.upload(
                        response.content,
                        public_id=f'{username}_profile',
                        folder='ucode/profile_images',
                        resource_type='image'
                    )
                    user.profile_image = upload_result['public_id']
                else:
                    user.profile_image = 'ucode/profile_images/hyqi9y5ucjmgigtlrmth'
            user.save()
            is_new_user = True

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'profile_image': user.profile_image if is_new_user else user.profile_image.public_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'is_new_user': is_new_user  # Flag to indicate if user was created
        }
