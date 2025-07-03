from django.contrib.auth.models import AbstractUser
from django.db import models
from cloudinary.models import CloudinaryField


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    profile_image = CloudinaryField('image', folder='ucode/profile_images',
                                    default='ucode/profile_images/hyqi9y5ucjmgigtlrmth', overwrite=True)
    list_display = ('username', 'email', 'date', 'profile_image')

    def __str__(self):
        return self.username


class UserCourse(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    progress = models.PositiveIntegerField(default=0)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.course.name}'


class UserLesson(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    score = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.user.username} - {self.lesson.title}'


class UserAnswer(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    question = models.ForeignKey('courses.CodingQuestion', on_delete=models.CASCADE)
    answer = models.TextField()
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.username} - {self.question.question}'
