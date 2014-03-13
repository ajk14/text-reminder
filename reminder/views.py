
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound
from django.utils import timezone
from reminder.models import Reminder, User
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil import parser 
from random import randint
from twilio.rest import TwilioRestClient
import time
import dateutil.tz
import pytz
import re

MINUTE_CHOICES = ["00", "05", "10", "15", "20", "25", "30", "35", "40", "45", "50", "55"]
HOUR_CHOICES = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]

def home(request):
    context = {}
    context['minutes'] = MINUTE_CHOICES
    context['hours'] = HOUR_CHOICES

    if request.POST:   
        if 'phone_form' in request.POST:
            return validate_phone(request, context)
        else:
            return create_reminder(request, context)
    return render(request, 'templates/index.html', context)

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
    provided_phone = request.POST['phone']
    time_string = str(request.POST['date']) + " " + str(request.POST['hour']) + ":" + str(request.POST['minute']) + str(request.POST['ampm'])

    try:
        timezone = dateutil.tz.gettz(request.POST['timezone'])
        reminder_datetime = parser.parse(time_string).replace(tzinfo=timezone)
        Reminder.objects.create(message=request.POST['message'], 
                                phone=provided_phone, 
                                time=reminder_datetime)
    except:
        return HttpResponse("<h1> FORM INVALID </h1>")

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

def send_activation(request, phone):
    id = randint(1000000, 9999999) #7 digit numbers w/o leading 0                                
    client = TwilioRestClient(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)
    message = client.sms.messages.create(body="Your confirmation code for TextMyAlerts.com is: " +
                                         str(id),
                                         to=phone,
                                         from_=settings.TWILIO_NUMBER)
    return id


def receive(request):
    context = {}
    phone = request.GET.get('From')
    body = request.GET.get('Body')
    
    delta = int(re.sub("\D", "", body))
    print delta
    print body
 
    if 'h' in body or 'H' in body:
        delta *= 60
    if 'd' in body or 'D' in body:
        delta *= 1440
    
    print delta

    user = User.objects.get(phone=phone)
    reminder = user.getLatestReminder()

    snooze = timedelta(minutes=delta)
    reminder.time = datetime.now() + snooze
    reminder.sent = False
    reminder.save()

    return render(request, 'templates/twilio.html', context)
  


def remind(request):
    reminders = Reminder.objects.all()
    for reminder in reminders:
        if not reminder.sent:
            try:
                user = User.objects.get(phone=reminder.phone)
            except:
                continue
            if not user.isActive:
                continue
            reminder_datetime = reminder.time
            
            now = datetime.utcnow().replace(tzinfo = pytz.utc)
            if reminder_datetime.astimezone(pytz.utc) < now:
                client = TwilioRestClient(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)
                try:
                    message = client.sms.messages.create(body=reminder.message,
                                                         to=reminder.phone,
                                                         from_=settings.TWILIO_NUMBER)
                except:
                    print "Failed to send reminder"
                reminder.sent = True
                reminder.save()
    return HttpResponse("Worked!")
