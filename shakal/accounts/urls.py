# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from forms import RegistrationFormUniqueEmail, AuthenticationRememberForm
from shakal.accounts import views as shakal_views

class Pattenrs(object):
	def __init__(self):
		self.app_name = 'accounts'
		self.name = 'accounts'
		self.register_context = {
			'form_class': RegistrationFormUniqueEmail,
			'backend': 'registration.backends.default.DefaultBackend'}

	@property
	def urls(self):
		urlpatterns = patterns('',
			url(r'^(?P<pk>[0-9]+)/', shakal_views.profile, name = 'auth_profile'),
			url(r'^register/$', 'registration.views.register', self.register_context, name = 'registration_register'),
			url(r'^login/$', shakal_views.login, {'template_name' : 'registration/login.html', 'authentication_form': AuthenticationRememberForm}, name = 'auth_login'),
			url(r'^', include('registration.backends.default.urls')),
		)
		return urlpatterns


urlpatterns = Pattenrs().urls