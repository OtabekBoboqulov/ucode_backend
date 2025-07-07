from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from user.views import SignupView, CustomTokenObtainPairView, LogoutView, user_courses
from courses.views import courses_index, courses_create, courses_details, lessons_details

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('courses/', courses_index),
    path('courses/<int:course_id>/', courses_details),
    path('courses/create/', courses_create),
    path('courses/enrolled/', user_courses),
    path('lessons/<int:lesson_id>/', lessons_details),
]