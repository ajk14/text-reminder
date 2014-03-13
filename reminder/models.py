from django.db import models

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
