from django.contrib import admin
from .models import *

admin.site.register(Course)
admin.site.register(Lesson)
admin.site.register(Video)
admin.site.register(Text)
admin.site.register(MultipleChoiceQuestion)
admin.site.register(MultipleOptionsQuestion)
admin.site.register(CodingQuestion)
admin.site.register(MultipleChoiceOption)
admin.site.register(MultipleOptionsOption)
admin.site.register(CodingTest)
