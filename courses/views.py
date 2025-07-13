import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Course, Lesson, Component, MultipleChoiceQuestion, MultipleOptionsQuestion, Video, Text, \
    MultipleChoiceOption, MultipleOptionsOption
from user.models import UserLesson, UserComponent, UserCourse
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def lessons_start(request, lesson_id):
    if UserLesson.objects.filter(user=request.user, lesson=lesson_id).exists():
        return Response({'message': 'Lesson already started'})
    lesson = Lesson.objects.get(id=lesson_id)
    user_lesson = UserLesson(user=request.user, lesson=lesson)
    user_lesson.score = sum(
        [component.max_score for component in lesson.components.all() if component.type in ['video', 'text']])
    user_lesson.save()
    return Response(
        {
            'message': 'Lesson started successfully',
            'lesson': LessonSerializer(lesson).data
        }
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lessons_next(request, course_id, serial_number):
    course = Course.objects.get(id=course_id)
    if course.lessons.all().filter(serial_number=serial_number + 1).exists():
        lesson = course.lessons.get(serial_number=serial_number + 1)
        id = lesson.id
        return Response({'id': id})
    else:
        return Response({'id': 0})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def task_check(request, component_id):
    component = Component.objects.get(id=component_id)
    user_lesson = UserLesson.objects.get(user=request.user, lesson=component.lesson)
    user_course = UserCourse.objects.get(user=request.user, course=component.lesson.course)
    has_user_component = UserComponent.objects.filter(user=request.user, component=component).exists()
    is_correct = False
    if has_user_component:
        user_component = UserComponent.objects.get(user=request.user, component=component)
        user_lesson.score -= user_component.score
    else:
        user_component = UserComponent(user=request.user, component=component)
    if component.type == 'mcq':
        if request.data['answer'] == 'true':
            user_lesson.score += component.max_score
            user_component.score = component.max_score
            is_correct = True
        else:
            user_component.score = 0
    elif component.type == 'moq':
        moq_component = MultipleOptionsQuestion.objects.get(id=component_id)
        answers = len([1 for option in moq_component.options.all() if option.is_correct])
        user_answer = request.data['answer']
        if len(user_answer) == answers and 'false' not in user_answer:
            user_lesson.score += component.max_score
            user_component.score = component.max_score
            is_correct = True
        else:
            user_component.score = 0
    user_component.save()
    if user_lesson.score >= 80:
        user_lesson.is_completed = True
        user_course.progress += component.lesson.max_score
        if user_course.progress >= 100:
            user_course.is_completed = True
        user_course.save()
    elif user_lesson.is_completed:
        user_course.progress -= component.lesson.max_score
        user_lesson.is_completed = False
        user_course.save()
    else:
        user_lesson.is_completed = False
    user_lesson.save()
    return Response({'is_correct': is_correct})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def courses_lessons(request, course_id):
    course = Course.objects.get(id=course_id)
    lessons = course.lessons.all().order_by('serial_number')
    lessons_serialized = LessonSerializer(lessons, many=True)
    return Response(lessons_serialized.data)


@api_view(['POST'])
@staff_required
def lessons_create(request):
    data = request.data
    course = Course.objects.get(id=data['course_id'])
    lesson = Lesson(course=course, serial_number=data['serial_number'], title=data['title'],
                    max_score=data['max_score'])
    if data.get('lesson_materials'):
        lesson.lesson_materials = data['lesson_materials']
    lesson.save()
    components = json.loads(data['components'])
    for component in components:
        if component['type'] == 'video':
            video_component = Video(lesson=lesson, max_score=component['max_score'],
                                    serial_number=component['serial_number'], video_url=component['video_url'])
            video_component.save()
        elif component['type'] == 'text':
            text_component = Text(lesson=lesson, max_score=component['max_score'],
                                  serial_number=component['serial_number'], content=component['content'])
            text_component.save()
        elif component['type'] == 'mcq':
            mcq_component = MultipleChoiceQuestion(lesson=lesson, max_score=component['max_score'],
                                                   serial_number=component['serial_number'],
                                                   question=component['question'])
            mcq_component.save()
            for option in component['options']:
                mcq_option = MultipleChoiceOption(question=mcq_component, is_correct=option['is_correct'],
                                                  option=option['option'])
                mcq_option.save()
        elif component['type'] == 'moq':
            moq_component = MultipleOptionsQuestion(lesson=lesson, max_score=component['max_score'],
                                                    serial_number=component['serial_number'],
                                                    question=component['question'])
            moq_component.save()
            for option in component['options']:
                moq_option = MultipleOptionsOption(question=moq_component, is_correct=option['is_correct'],
                                                   option=option['option'])
                moq_option.save()
    return Response({'message': 'Lesson created successfully'})
