from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Course, Lesson
from api.serializers import CourseSerializer, LessonSerializer, UserLessonSerializer
from api.decorators import staff_required


@api_view(['GET'])
def courses_index(request):
    courses = Course.objects.all().order_by('-created_at')
    courses_serialized = CourseSerializer(courses, many=True)
    return Response(courses_serialized.data)


@api_view(['POST'])
@staff_required
def courses_create(request):
    course_serialized = CourseSerializer(data=request.data)
    if course_serialized.is_valid():
        course_serialized.save()
        return Response(course_serialized.data)
    return Response(course_serialized.errors)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def courses_details(request, course_id):
    course = Course.objects.get(id=course_id)
    if request.user not in course.learners.all():
        course.learners.add(request.user)
    course_serialized = CourseSerializer(course)
    lessons = course.lessons.all().order_by('serial_number')
    lessons_serialized = LessonSerializer(lessons, many=True)
    return Response({'course': course_serialized.data, 'lessons': lessons_serialized.data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lessons_details(request, lesson_id):
    lesson = Lesson.objects.get(id=lesson_id)
    lesson_serialized = LessonSerializer(lesson)
    return Response(lesson_serialized.data)
