from django.db import models

class Reminder(models.Model):
    message = models.CharField(max_length=180)
    phone = models.CharField(max_length=20)
    hour = models.IntegerField()
    minute = models.IntegerField()
    ampm = models.CharField(max_length=2)
    date = models.DateField()
