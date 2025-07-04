from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Course
from api.serializers import CourseSerializer
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
