from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
from reminder.forms import ReminderForm
from reminder.models import Reminder
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser 
from twilio.rest import TwilioRestClient
import time
import dateutil.tz
import pytz

MINUTE_CHOICES = ["00", "05", "10", "15", "20", "25", "30", "35", "40", "45", "50", "55"]
HOUR_CHOICES = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
TIMEZONE_CHOICES = ["PST8PDT", "MST7MDT", "CST6CDT", "EST5EDT"]

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
        time_string = str(reminder.date) + " " + str(reminder.hour) + ":" + str(reminder.minute) + str(reminder.ampm)
        print reminder.timezone
        timezone = dateutil.tz.gettz(reminder.timezone)
        reminder_datetime = parser.parse(time_string).replace(tzinfo=timezone)
        now = datetime.utcnow().replace(tzinfo = pytz.utc)
        if reminder_datetime.astimezone(pytz.utc) < now:
            print "TIME IN THE PAST"
            print "TIMEZONE" + str(timezone)
            print "DATETIME" + str(reminder_datetime.astimezone(pytz.utc))
            print "NOW" + str(now)
            client = TwilioRestClient(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)
            try:
                message = client.sms.messages.create(body=reminder.message,
                                             to=reminder.phone,
                                             from_=settings.TWILIO_NUMBER)
            except:
                print "Failed to send reminder"
            reminder.delete()
        else:
            print "TIME IN FUTURE"
    return HttpResponse("Worked!")
