from django.forms import ModelForm
from reminder.models import Reminder

# Create the form class.
class ReminderForm(ModelForm):
    class Meta:
        model = Reminder
