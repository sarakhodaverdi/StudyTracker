from typing import Container
from django.db import models
from django.contrib.auth.models import User

class Subject(models.Model):
    user = models.ForeignKey(User,on_delete = models.CASCADE)
    name = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'name'],
            name='unique_user_subject')
        ]

    def __str__(self):
        return self.name
    
class StudySession(models.Model):
    subject = models.ForeignKey(Subject,on_delete=models.CASCADE)
    date = models.DateField()
    hours = models.DecimalField(max_digits=4,decimal_places=2)

    def __str__(self):
        return self.name
    