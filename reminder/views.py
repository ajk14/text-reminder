from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from reminder.forms import ReminderForm
from reminder.models import Reminder
from datetime import datetime
from twilio.rest import TwilioRestClient
import time

def home(request):
    context = {}
    reminder_form = ReminderForm()
    context['reminder_form'] = reminder_form

    if request.POST:   
        reminder_form = ReminderForm(request.POST)
        if reminder_form.is_valid:
            reminder_form.save()
            context['success'] = True
            return render(request, 'templates/index.html', context)
    return render(request, 'templates/index.html', context)

def remind(request):
    reminders = Reminder.objects.all()
    for reminder in reminders:
        time_string = str(reminder.date) + " " + str(reminder.hour) + " " + str(reminder.minute) + str(reminder.ampm)
        reminder_datetime = datetime.strptime(time_string, "%Y-%m-%d %I %M%p")
        print reminder_datetime
        if reminder_datetime <= datetime.now():
            print str(reminder.date) + " " + str(reminder_datetime) + " About to remind!"
            client = TwilioRestClient(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)
            message = client.sms.messages.create(body=reminder.message,
                                             to=reminder.phone,
                                             from_=settings.TWILIO_NUMBER)
            reminder.delete()
    return HttpResponse("Worked!")
