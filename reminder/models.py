from django.db import models
from twilio.rest import TwilioRestClient
from random import randint
import dateutil.tz

class Reminder(models.Model):
    message = models.CharField(max_length=180)
    phone = models.CharField(max_length=20)
    time = models.DateTimeField()
    sent = models.BooleanField(default=False)

class User(models.Model):
    phone = models.CharField(max_length=20)
    confirmation = models.IntegerField(null=True)
    isActive = models.BooleanField()

    def getLatestReminder(self):
        myReminders = Reminder.objects.filter(phone=self.phone, sent=True)
        latestReminder = myReminders[0]
        for reminder in myReminders:
            if reminder.time > latestReminder.time:
                latestReminder = reminder
        return latestReminder

    def createInactiveUser(phone):
        user = User.objects.create(phone=provided_phone, isActive=False)
        activation_key = send_activation(request, provided_phone)
        user.confirmation = activation_key
        user.save()
        return user
