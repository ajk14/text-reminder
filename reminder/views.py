from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound
from django.utils import timezone
from reminder.forms import ReminderForm
from reminder.models import Reminder, User
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser 
from random import randint
from twilio.rest import TwilioRestClient
import time
import dateutil.tz
import pytz

MINUTE_CHOICES = ["00", "05", "10", "15", "20", "25", "30", "35", "40", "45", "50", "55"]
HOUR_CHOICES = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]

def home(request):
    context = {}
    reminder_form = ReminderForm()
    context['reminder_form'] = reminder_form
    context['minutes'] = MINUTE_CHOICES
    context['hours'] = HOUR_CHOICES

    if request.POST:   
        if 'phone_form' in request.POST:
            return validate_phone(request, context)
        else:
            return create_reminder(request, context)
    return render(request, 'templates/index.html', context)

def receive(request):
    context = {}
    print request.POST
    return HttpResponse("Worked..." + str(request.POST))


def validate_phone(request, context):
    phone = request.POST['phone']
    print request.POST
    try:
        user = User.objects.get(phone=phone)
    except:
        return HttpResponseNotFound('<h1>User not found</h1>')
    provided_key = request.POST['code']
    if user.confirmation == int(provided_key):
        user.isActive=True
        user.save()
    else:
        return HttpResponseNotFound('<h1>Invalid key</h1>')
    context['success'] = True
    return render(request, 'templates/index.html', context)

def create_reminder(request, context):
    reminder_form = ReminderForm(request.POST)
    print request.POST
    if reminder_form.is_valid():
        reminder_form.save()
        provided_phone = reminder_form.cleaned_data["phone"]
        try:
            user = User.objects.get(phone=provided_phone)
        except:
            user = User.objects.create(phone=provided_phone, isActive=False)
        if not user.isActive:
            activation_key = send_activation(request, provided_phone)
            user.confirmation = activation_key
            user.save()
            context["activating"] = True
            context["phone"] = provided_phone
            return render(request, 'templates/index.html', context)
        context['success'] = True
        return render(request, 'templates/index.html', context)
    else:
        return HttpResponseNotFound('<h1>INVALID FORM</h1>')


def send_activation(request, phone):
    id = randint(1000000, 9999999) #7 digit numbers w/o leading 0                                
    client = TwilioRestClient(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)
    message = client.sms.messages.create(body="Your confirmation code for TextMyAlerts.com is: " +
                                         str(id),
                                         to=phone,
                                         from_=settings.TWILIO_NUMBER)
    return id

def remind(request):
    reminders = Reminder.objects.all()
    for reminder in reminders:
        try:
            user = User.objects.get(phone=reminder.phone)
        except:
            continue
        if not user.isActive:
            continue
        time_string = str(reminder.date) + " " + str(reminder.hour) + ":" + str(reminder.minute) + str(reminder.ampm)

        #timezone = dateutil.tz.gettz(TIMEZONE_CHOICES[reminder.timezone])
        timezone = dateutil.tz.gettz(reminder.timezone)
        reminder_datetime = parser.parse(time_string).replace(tzinfo=timezone)

        now = datetime.utcnow().replace(tzinfo = pytz.utc)
        if reminder_datetime.astimezone(pytz.utc) < now:
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
