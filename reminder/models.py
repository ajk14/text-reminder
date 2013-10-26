from django.db import models

AMPM_CHOICES = (('AM','AM'), ('PM','PM'))
class Reminder(models.Model):
    message = models.CharField(max_length=180)
    phone = models.CharField(max_length=20)
    time = models.TimeField()
    ampm = models.CharField(max_length=2, choices=AMPM_CHOICES)
    date = models.DateField()