from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from user.views import SignupView, CustomTokenObtainPairView, LogoutView
from courses.views import courses_index, courses_create

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('courses/', courses_index),
    path('courses/create/', courses_create),
]