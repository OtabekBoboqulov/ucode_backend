import base64
import json
import uuid
from io import BytesIO
import qrcode
from django.http import HttpResponse
from django.template.loader import render_to_string
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from weasyprint import HTML
from django.conf import settings

from .models import Course, Lesson, Component, MultipleChoiceQuestion, MultipleOptionsQuestion, Video, Text, \
    MultipleChoiceOption, MultipleOptionsOption, Certificate
from user.models import UserLesson, UserComponent, UserCourse
from api.serializers import CourseSerializer, LessonSerializer, UserLessonSerializer, CertificateSerializer
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


@api_view(['DELETE'])
@staff_required
def courses_delete(request, course_id):
    course = Course.objects.get(id=course_id)
    course.delete()
    return Response({'message': 'Kurs muvaffaqiyatli o`chirildi'})


@api_view(['GET', 'PUT'])
@staff_required
def courses_update(request, course_id):
    course = Course.objects.get(id=course_id)
    if request.method == 'GET':
        course_serialized = CourseSerializer(course)
        return Response(course_serialized.data)
    elif request.method == 'PUT':
        course_serialized = CourseSerializer(course, data=request.data)
        if course_serialized.is_valid():
            course_serialized.save()
            return Response(course_serialized.data)
        return Response(course_serialized.errors)
    return Response({'message': 'Method not allowed'})


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


@api_view(['DELETE'])
@staff_required
def lessons_delete(request, lesson_id):
    course = Lesson.objects.get(id=lesson_id)
    course.delete()
    return Response({'message': 'Dars muvaffaqiyatli o`chirildi'})


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
    if request.data.get('lessonId'):
        try:
            lesson = Lesson.objects.get(id=request.data['lessonId'])
            lesson.delete()
        except Lesson.DoesNotExist:
            return Response({'message': 'Lesson not found'}, status=status.HTTP_404_NOT_FOUND)
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


class GenerateCertificateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        try:
            course = Course.objects.get(id=course_id)
            user = request.user

            user_course = UserCourse.objects.get(user=user, course=course)
            if not user_course.is_completed:
                return Response({'message': 'Kurs kugatilmagan'}, status=status.HTTP_400_BAD_REQUEST)

            if Certificate.objects.filter(student=user, course=course).exists():
                certificate = Certificate.objects.get(student=user, course=course)
                certificate_id = certificate.certificate_id
            else:
                certificate_id = str(uuid.uuid4())
                certificate = Certificate.objects.create(
                    student=user,
                    course=course,
                    certificate_id=certificate_id
                )

            serializer = CertificateSerializer(certificate)

            verification_data = (f'Sertifikat {user.get_full_name()}ga {course.name} kursini muvaffaqiyatli yakunlaganu'
                                 f' uchun {certificate.issue_date} sanasida berildi')
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(verification_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="darkblue", back_color="white")
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            qr_code_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

            context = {
                'recipient_name': user.get_full_name() or user.username,
                'course_name': course.name,
                'issue_date': certificate.issue_date.strftime('%B %d, %Y'),
                'certificate_id': certificate_id,
                'qr_code': qr_code_base64,
            }
            html_string = render_to_string('certificate_template.html', context)

            # Generate PDF, respecting the template's @page settings
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="certificate_{certificate.certificate_id}.pdf"'
            HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(
                response,
                stylesheets=[],
                presentational_hints=True,
                margin_left=0,
                margin_right=0,
                margin_top=0,
                margin_bottom=0
            )

            return response
        except Course.DoesNotExist:
            return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)
        except UserCourse.DoesNotExist:
            return Response({'message': 'User course not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def verify_certificate(request, certificate_id):
    try:
        certificate = Certificate.objects.get(certificate_id=certificate_id)
        certificate_serialized = CertificateSerializer(certificate)
        return Response(certificate_serialized.data)
    except Certificate.DoesNotExist:
        return Response({'message': 'Sertifikat mavjud emas'}, status=status.HTTP_404_NOT_FOUND)
