from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from user.views import SignupView, CustomTokenObtainPairView, GoogleAuthView, LogoutView, user_courses, user_update, \
    statistics
from courses.views import (
    courses_index, courses_create, courses_details, lessons_details, lessons_start, task_check, courses_lessons,
    lessons_next, lessons_create, courses_delete, lessons_delete, GenerateCertificateView, courses_update,
    verify_certificate
)

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('google-auth/', GoogleAuthView.as_view(), name='google-auth'),
    path('courses/', courses_index),
    path('courses/<int:course_id>/', courses_details),
    path('courses/<int:course_id>/lessons/', courses_lessons),
    path('courses/<int:course_id>/next-lesson/<int:serial_number>/', lessons_next),
    path('courses/delete/<int:course_id>/', courses_delete),
    path('courses/update/<int:course_id>/', courses_update),
    path('courses/certificate/<int:course_id>/', GenerateCertificateView.as_view()),
    path('courses/create/', courses_create),
    path('courses/enrolled/', user_courses),
    path('lessons/<int:lesson_id>/', lessons_details),
    path('lessons/<int:lesson_id>/start/', lessons_start),
    path('lessons/delete/<int:lesson_id>/', lessons_delete),
    path('lessons/create/', lessons_create),
    path('task-check/<int:component_id>/', task_check),
    path('profile/edit/', user_update),
    path('verify-certificate/<str:certificate_id>/', verify_certificate),
    path('statistics/', statistics),
]
