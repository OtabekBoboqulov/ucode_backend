from django.utils import timezone
from datetime import datetime
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from drf_polymorphic.serializers import PolymorphicSerializer
from user.models import CustomUser, UserLesson
from courses.models import (
    Course, Lesson, Component, Video, Text, MultipleChoiceQuestion, MultipleOptionsQuestion, CodingQuestion,
    MultipleChoiceOption, MultipleOptionsOption, CodingTest
)


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
        fields = ('question', 'tests', 'students')


# Component Serializer with custom logic
class ComponentSerializer(serializers.ModelSerializer):
    data = serializers.SerializerMethodField()

    class Meta:
        model = Component
        fields = ('id', 'lesson', 'type', 'max_score', 'serial_number', 'data')

    def get_data(self, obj):
        print(f"Serializing component: id={obj.id}, type={obj.type}, model={type(obj).__name__}")
        # Cast to child model based on type
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
                print(f"Cast to child model: {type(child_instance).__name__}")
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
                print(f"Child model {child_model.__name__} not found for id={obj.id}")
                return {}
        print(f"No matching child model for type={obj.type}")
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
