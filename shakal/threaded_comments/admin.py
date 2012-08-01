# -*- coding: utf-8 -*-

from django.contrib import admin
from django.contrib.comments.models import Comment
from django.contrib.comments.admin import CommentsAdmin
from django.utils.translation import ugettext_lazy as _
from shakal.threaded_comments.models import ThreadedComment

class ThreadedCommentsAdmin(CommentsAdmin):
	fieldsets = (
		(None,
			{'fields': ('content_type', 'object_pk', 'site')}
		),
		(_('Content'),
			{'fields': ('subject', 'user', 'user_name', 'user_email', 'user_url', 'comment')}
		),
		(_('Metadata'),
			{'fields': ('submit_date', 'ip_address', 'is_public', 'is_removed', 'is_locked')}
		),
	)
	list_display = ('subject', 'name', 'content_type', 'ip_address', 'submit_date', 'is_public', 'is_removed', 'is_locked')

admin.site.unregister(Comment)
admin.site.register(ThreadedComment, ThreadedCommentsAdmin)