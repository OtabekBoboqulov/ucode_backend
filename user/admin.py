from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, UserCourse, UserLesson


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('profile_image', )}),
    )


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(UserCourse)
admin.site.register(UserLesson)
