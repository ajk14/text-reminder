from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound
from django.utils import timezone
from django.utils.datastructures  import MultiValueDictKeyError
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
from reminder.models import Reminder, User
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil import parser 
from random import randint
from twilio.rest import TwilioRestClient
import json
import time
import dateutil.tz
import pytz
import re

MINUTE_CHOICES = ["00", "05", "10", "15", "20", "25", "30", "35", "40", "45", "50", "55"]
HOUR_CHOICES = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]


###########################
# Specific to Web Client
###########################
def home(request):
    context = {}
    context['minutes'] = MINUTE_CHOICES
    context['hours'] = HOUR_CHOICES

    if request.POST:   
        if 'phone_form' in request.POST:
            return confirm_phone_web(request, context)
        else:
            return create_reminder_web(request, context)
    return render(request, 'templates/index.html', context)

def confirm_phone_web(request, context):
    try:
        confirm_phone(request)
    except User.DoesNotExist:
        return HttpResponseNotFound('<h1>User not found</h1>')
    except Exception:
        return HttpResponseNotFound('<h1>Invalid key</h1>')
    
    context['success'] = True
    return render(request, 'templates/index.html', context)

def create_reminder_web(request, context):
    try:
        createReminder(request.POST['date'], request.POST['hour'], 
                       request.POST['minute'], request.POST['ampm'], 
                       request.POST['timezone'], request.POST['message'],
                       request.POST['phone'])
    except Exception as e:
        return HttpResponse("<h1> FORM INVALID </h1>")

    try:
        user = User.objects.get(phone=request.POST['phone'])
    except:
        try:
            createInactiveUser(request.POST['phone'])
        except:
            return HttpResponse("<h1>Invalid Phone Number </h1>")
        context["activating"] = True
        context["phone"] = request.POST['phone']
        return render(request, 'templates/index.html', context)

    context['success'] = True
    return render(request, 'templates/index.html', context)


###########################
# Platform Agnostic
###########################

# Parameters Required: Phone, Activation Code
@csrf_exempt
def confirm_phone_json(request):
    try:
        confirm_phone(request) 
    except User.DoesNotExist:
        return HttpResponse(json.dumps({'userExists':False}), 'application/json')
    except Exception:
        return HttpResponse(json.dumps({'userExists':True, 
                                              'validKey':False}), 'application/json')
    return HttpResponse(json.dumps({'userExists':True, 'validKey':True}), 
                        'application/json')

@csrf_exempt
def create_reminder_json(request):
    try:
        createReminder(request.POST['date'], request.POST['hour'],
                       request.POST['minute'], request.POST['ampm'],
                       request.POST['timezone'], request.POST['message'],
                       request.POST['phone'])
    except Exception as e:
        return HttpResponse(json.dumps({'validForm':False}), 'application/json')

    try:
        user = User.objects.get(phone=request.POST['phone'])
    except:
        try:
            createInactiveUser(request.POST['phone'])
        except:
            return HttpResponse(json.dumps({'validForm':False}), 'application/json')
        return HttpResponse(json.dumps({'validForm':True, 'activationSent':True}),
                            'application/json')
    return HttpResponse(json.dumps({'validForm':True, 'activationSent':False}),
                        'application/json')   

##############################
# Server-side only methods
##############################

def send_activation(phone):
    id = randint(1000000, 9999999) #7 digit numbers w/o leading 0                                
    client = TwilioRestClient(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)
    message = client.sms.messages.create(body="Your confirmation code for TextMyAlerts.com is: " +
                                         str(id),
                                         to=phone,
                                         from_=settings.TWILIO_NUMBER)
    return id

def createInactiveUser(phone):
        user = User.objects.create(phone=phone, isActive=False)
        activation_key = send_activation(phone)
        user.confirmation = activation_key
        user.save()
        return user

def createReminder(date, hour, minute, ampm, timezone, message, phone):
    time_string = date + " " + hour + ":" + minute + ampm
    timezone = dateutil.tz.gettz(timezone)
    reminder_datetime = parser.parse(time_string).replace(tzinfo=timezone)
    reminder = Reminder.objects.create(message=message,
                                       phone=phone,
                                       time=reminder_datetime)
    return reminder

def confirm_phone(request):
    phone = request.POST['phone']
    key = request.POST['code']

    user = User.objects.get(phone=phone)

    if not is_valid_key(user, key):
        raise Exception("Invalid Key")

    user.isActive=True
    user.save()
    return 

def user_exists(phone):
    try:
        User.objects.get(phone=phone)
    except:
        return false
    return true

def is_valid_key(user, key):
    return (user.confirmation == int(key))

def receive(request):
    context = {}
    phone = request.GET.get('From')[-10:]
    body = request.GET.get('Body')
    
    delta = int(re.sub("\D", "", body))
    print phone
 
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
