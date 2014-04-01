from django.conf.urls import patterns, include, url
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'reminder.views.home', name='home'),
    url(r'^remind/', 'reminder.views.remind', name='remind'),
    url(r'^receive/', 'reminder.views.receive', name='receive'),
    url(r'^confirm/', 'reminder.views.confirm_phone_json', name='confirm'),
    url(r'^create/', 'reminder.views.create_reminder_json', name='create'),
    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    # url(r'^reminder/', include('reminder.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
