from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
import cloudinary.uploader
from api.serializers import SignupSerializer, CustomTokenObtainPairSerializer, CourseSerializer, GoogleAuthSerializer
from .models import CustomUser
from courses.models import Course


class GoogleAuthView(generics.CreateAPIView):
    serializer_class = GoogleAuthSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK if not result['is_new_user'] else status.HTTP_201_CREATED)


class SignupView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_courses(request):
    courses = request.user.courses.all()
    course_ids = [course.id for course in courses]
    courses_serialized = CourseSerializer(courses, many=True)
    return Response({'enrolled_courses_ids': course_ids, 'enrolled_courses': courses_serialized.data})


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def user_update(request):
    user = request.user
    data = request.data
    user.first_name = data['first_name']
    user.last_name = data['last_name']
    user.username = data['username']
    user.email = data['email']
    if data.get('profile_image'):
        if user.profile_image != 'ucode/profile_images/hyqi9y5ucjmgigtlrmth':
            cloudinary.uploader.destroy(user.profile_image.public_id)
        user.profile_image = data['profile_image']
    user.save()
    image_url = user.profile_image.url
    return Response({'message': 'User updated successfully', 'profile_image': image_url})
