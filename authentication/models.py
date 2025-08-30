from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    id = models.CharField(max_length=100, primary_key=True)
    role = models.CharField(max_length=50, default='student', choices=[('student', 'Student'), ('teacher', 'Teacher'), ('admin', 'Admin')])

    def __str__(self):
        return self.user.username