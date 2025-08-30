from django.db import models
from django.contrib.auth.models import User


class studentGroup(models.Model):
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    students = models.ManyToManyField(User)
    no_of_students = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class FileDetail(models.Model):
    file_id = models.CharField(max_length=64, unique=True, editable=False)
    file = models.FileField(upload_to='uploads/')
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    file_upload_date = models.DateTimeField(auto_now_add=True)
    file_expiry_date = models.DateTimeField(null=True, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    sharing_policy = models.CharField(max_length=20, choices=[
        ('private', 'Private'),
        ('public', 'Public'),
        ('shared', 'Shared')
    ], default='private')
    access_type = models.CharField(max_length=20, choices=[
        ('view', 'View Only'),
        ('download', 'Downloadable')
    ], default='view')
    shared_group = models.ForeignKey(studentGroup, blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.file_id}"