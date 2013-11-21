from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from reminder.forms import ReminderForm
from reminder.models import Reminder
from datetime import datetime
from dateutil import parser
from twilio.rest import TwilioRestClient
import time

MINUTE_CHOICES = ["00", "05", "10", "15", "20", "25", "30", "35", "40", "45", "50", "55"]
HOUR_CHOICES = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
TIMEZONE_CHOICES = ["PST", "MST", "CST", "EST"]

def home(request):
    context = {}
    reminder_form = ReminderForm()
    context['reminder_form'] = reminder_form
    context['minutes'] = MINUTE_CHOICES
    context['hours'] = HOUR_CHOICES
    context['timezones'] = TIMEZONE_CHOICES

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
        time_string = str(reminder.date) + " " + str(reminder.hour) + ":" + str(reminder.minute) + str(reminder.ampm) + str(reminder.timezone)
        print time_string
        reminder_datetime = parser.parse(time_string)
        #reminder_datetime = datetime.strptime(time_string, "%Y-%m-%d %I %M%p %Z")
        print reminder_datetime
        if reminder_datetime <= datetime.now():
            print str(reminder.date) + " " + str(reminder_datetime) + " About to remind!"
            client = TwilioRestClient(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)
            try:
                message = client.sms.messages.create(body=reminder.message,
                                             to=reminder.phone,
                                             from_=settings.TWILIO_NUMBER)
            except:
                print "Failed to send reminder"
            reminder.delete()
    return HttpResponse("Worked!")
