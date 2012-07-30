# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
import views as survey_views

class Patterns(object):
	def __init__(self):
		self.app_name = 'survey'
		self.name = 'survey'

	@property
	def urls(self):
		urlpatterns = patterns('',
			url(r'^$', survey_views.survey_list, name = 'list'),
			url(r'^zoznam/(?P<page>\d+)/', survey_views.survey_list, name = 'list-page'),
			url(r'^post/(?P<pk>\d+)/$', survey_views.post, name = 'post'),
			url(r'^vytvorit/$', survey_views.create, name = 'create'),
			url(r'^detail/(?P<slug>[-\w]+)/$', survey_views.survey_detail_by_slug, name = "detail-by-slug"),
		)
		return (urlpatterns, self.app_name, self.name)

urlpatterns = Patterns().urls