from django.core.validators import MaxValueValidator
from django.db import models
from cloudinary.models import CloudinaryField
from user.models import CustomUser, UserCourse, UserLesson, UserComponent


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
    lesson_materials = CloudinaryField('materials', folder='ucode/lesson_materials', blank=True, null=True)

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
    student = models.ManyToManyField(CustomUser, related_name='components', through=UserComponent)

    def __str__(self):
        return f'{self.lesson}: {self.type}'


class Video(Component):
    video_url = models.URLField()

    def save(self, *args, **kwargs):
        self.type = 'video'
        super().save(*args, **kwargs)


class Text(Component):
    content = models.TextField()

    def save(self, *args, **kwargs):
        self.type = 'text'
        super().save(*args, **kwargs)


class MultipleChoiceQuestion(Component):
    question = models.TextField()

    def save(self, *args, **kwargs):
        self.type = 'mcq'
        super().save(*args, **kwargs)


class MultipleOptionsQuestion(Component):
    question = models.TextField()

    def save(self, *args, **kwargs):
        self.type = 'moq'
        super().save(*args, **kwargs)


class CodingQuestion(Component):
    LANGUAGE_CHOICES = (
        ('python', 'Python'),
        ('java', 'Java'),
        ('c', 'C'),
        ('c++', 'C++'),
        ('javascript', 'Javascript'),
    )
    language = models.CharField(max_length=15, choices=LANGUAGE_CHOICES, default='python')
    question = models.TextField()
    pre_written_code = models.TextField(blank=True, null=True)
    students = models.ManyToManyField(CustomUser, related_name='coding_questions', blank=True)

    def save(self, *args, **kwargs):
        self.type = 'coding'
        super().save(*args, **kwargs)


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
    input = models.TextField(blank=True, null=True)
    output = models.TextField()


class Certificate(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    issue_date = models.DateField(auto_now_add=True)
    certificate_id = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.student.username} - {self.course.name} - {self.certificate_id}"
