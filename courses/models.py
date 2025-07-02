from django.core.validators import MaxValueValidator
from django.db import models
from cloudinary.models import CloudinaryField
from user.models import CustomUser, UserCourse, UserLesson


class Course(models.Model):
    COMPLEXITY_CHOICES = (
        ('junior', 'Junior'),
        ('middle', 'Middle'),
        ('senior', 'Senior'),
    )
    name = models.CharField(max_length=250)
    complexity = models.CharField(max_length=250, choices=COMPLEXITY_CHOICES)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    banner_image = CloudinaryField('image', folder='ucode/course_banners',
                                   default='ucode/course_banners/ar96xy769kralsw28gu0', overwrite=True)
    learners = models.ManyToManyField(CustomUser, related_name='courses', through=UserCourse)

    def __str__(self):
        return f'{self.name} - {self.complexity}'


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=250)
    max_score = models.PositiveIntegerField(validators=[MaxValueValidator(100)])
    serial_number = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    students = models.ManyToManyField(CustomUser, related_name='lessons', through=UserLesson)

    def __str__(self):
        return f'{self.course.name}: {self.serial_number}. {self.title}'


class Component(models.Model):
    TYPE_CHOICES = (
        ('video', 'Video'),
        ('text', 'Text'),
        ('mcq', 'Multiple Choice'),
        ('moq', 'Multiple Options'),
        ('coding', 'Coding'),
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='components')
    type = models.CharField(max_length=15, choices=TYPE_CHOICES)
    max_score = models.PositiveIntegerField()
    serial_number = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.lesson}: {self.type}'


class Video(Component):
    video_url = models.URLField()
    type = 'video'


class Text(Component):
    content = models.TextField()
    type = 'text'


class MultipleChoiceQuestion(Component):
    question = models.TextField()
    type = 'mcq'


class MultipleOptionsQuestion(Component):
    question = models.TextField()
    type = 'moq'


class CodingQuestion(Component):
    question = models.TextField()
    type = 'coding'
    students = models.ManyToManyField(CustomUser, related_name='coding_questions')


class MultipleChoiceOption(models.Model):
    question = models.ForeignKey(MultipleChoiceQuestion, on_delete=models.CASCADE, related_name='options')
    option = models.TextField()
    is_correct = models.BooleanField(default=False)


class MultipleOptionsOption(models.Model):
    question = models.ForeignKey(MultipleOptionsQuestion, on_delete=models.CASCADE, related_name='options')
    option = models.TextField()
    is_correct = models.BooleanField(default=False)


class CodingTest(models.Model):
    question = models.ForeignKey(CodingQuestion, on_delete=models.CASCADE, related_name='tests')
    input = models.TextField()
    output = models.TextField()
