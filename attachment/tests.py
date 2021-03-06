# -*- coding: utf-8 -*-
import os

from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms.widgets import HiddenInput
from django.test import TestCase
from django.utils.encoding import smart_unicode

from .fields import AttachmentField
from .forms import TemporaryAttachmentFormMixin
from .models import UploadSession, Attachment, TemporaryAttachment
from .utils import get_available_size
from common_utils import get_meta
from common_utils.tests_common import ProcessFormTestMixin


class AttachmentModelTest(TestCase):
	def setUp(self):
		self.testContentType = ContentType.objects.all()[0]
		self.ct = get_meta(self.testContentType.model_class()).db_table

	def test_upload_session(self):
		session1 = UploadSession()
		session2 = UploadSession()
		self.assertNotEqual(session1.uuid, session2.uuid)

	def create_temporary_attachment(self, name, data):
		uploaded_file = SimpleUploadedFile(name, data)
		session = UploadSession()
		session.save()

		attachment = TemporaryAttachment(
			session = session,
			attachment = uploaded_file,
			content_type = ContentType.objects.get_for_model(TemporaryAttachment),
			object_id = session.id
		)
		return attachment

	def test_paths(self):
		try:
			attachment = self.create_temporary_attachment("test.txt", "")
			attachment.save()
			self.assertEqual(attachment.basename, "test.txt")
			self.assertEqual(attachment.name, "test.txt")
			self.assertEqual(attachment.url.index(settings.MEDIA_URL), 0)
			self.assertEqual(attachment.filename.index(settings.MEDIA_ROOT), 0)
			self.assertEqual(smart_unicode(attachment), attachment.attachment.name)
		finally:
			attachment.delete()

	def test_upload(self):
		try:
			file_data = b"0123456789"
			attachment = self.create_temporary_attachment("test.txt", file_data)
			attachment.save()

			saved_file_name = attachment.filename
			file_readed = open(saved_file_name, 'rb').read()
			self.assertEqual(file_data, file_readed)
		finally:
			attachment.delete()

	def test_delete(self):
		try:
			attachment = self.create_temporary_attachment("test.txt", "")
			attachment.save()
			saved_file_name = attachment.filename
			self.assertTrue(os.path.exists(saved_file_name))
		finally:
			attachment.delete()
		self.assertFalse(os.path.exists(saved_file_name))

	def test_replace_file(self):
		try:
			attachment = self.create_temporary_attachment("test.txt", b"A")
			attachment.save()

			file_readed = open(attachment.filename, 'rb').read()
			self.assertEqual(file_readed, "A")

			attachment.attachment = SimpleUploadedFile("test.txt", b"B")
			attachment.save()

			file_readed = open(attachment.filename, 'rb').read()
			self.assertEqual(file_readed, "B")
			self.assertEqual(attachment.basename, "test.txt")
		finally:
			attachment.delete()

	def test_upload_final(self):
		try:
			temp_attachment = self.create_temporary_attachment("test.txt", b"A")
			temp_attachment.save()

			attachment = Attachment(
				attachment = temp_attachment.attachment.name,
				content_type = ContentType.objects.get_for_model(UploadSession),
				object_id = 1
			)
			attachment.save()
			temp_attachment.delete()

			file_readed = open(attachment.filename, 'rb').read()
			self.assertEqual(file_readed, "A")
		finally:
			temp_attachment.delete_file()
			attachment.delete_file()

	def test_available_size(self):
		ctype = ContentType.objects.get_for_model(UploadSession)
		ctype_table = 'attachment_uploadsession'

		# unlimited
		with self.settings(ATTACHMENT_MAX_SIZE=-1, ATTACHMENT_SIZE_FOR_CONTENT={}):
			self.assertEqual(get_available_size(ctype, 0), -1)

		# base size
		with self.settings(ATTACHMENT_MAX_SIZE=10, ATTACHMENT_SIZE_FOR_CONTENT={}):
			self.assertEqual(get_available_size(ctype, 0), 10)

		# unlimited for content
		with self.settings(ATTACHMENT_MAX_SIZE=10, ATTACHMENT_SIZE_FOR_CONTENT={ctype_table: -1}):
			self.assertEqual(get_available_size(ctype, 0), -1)

		# limited size for content
		with self.settings(ATTACHMENT_MAX_SIZE=-1, ATTACHMENT_SIZE_FOR_CONTENT={ctype_table: 10}):
			self.assertEqual(get_available_size(ctype, 0), 10)

		# limited size for both
		with self.settings(ATTACHMENT_MAX_SIZE=10, ATTACHMENT_SIZE_FOR_CONTENT={ctype_table: 20}):
			self.assertEqual(get_available_size(ctype, 0), 20)

	def test_oversize(self):
		with self.settings(ATTACHMENT_MAX_SIZE=-1, ATTACHMENT_SIZE_FOR_CONTENT={'attachment_temporaryattachment': 2}):
			try:
				temp_attachment = self.create_temporary_attachment("test.txt", b"ABCD")
				with self.assertRaises(ValidationError):
					temp_attachment.size = temp_attachment.attachment.size
					temp_attachment.full_clean()
			finally:
				temp_attachment.delete_file()

			try:
				temp_attachment = self.create_temporary_attachment("test.txt", b"A")
				temp_attachment.size = temp_attachment.attachment.size
				temp_attachment.full_clean()
			finally:
				temp_attachment.delete_file()


class AttachmentFormTest(ProcessFormTestMixin, TestCase):
	def test_attachment_field(self):
		field = AttachmentField()
		field.widget.attrs['max_size'] = 2
		field.clean(SimpleUploadedFile("a.txt", "A")) #OK
		with self.assertRaises(ValidationError):
			field.clean(SimpleUploadedFile("a.txt", "ABC"))

	def test_render(self):
		field = AttachmentField()
		field.widget.attrs['max_size'] = 2
		field.widget.render("name", "")

	def create_attachment_form(self, data=None, files=None):
		ctype = ContentType.objects.get_for_model(UploadSession)
		ctype_table = 'attachment_uploadsession'

		class TestForm(TemporaryAttachmentFormMixin, forms.Form):
			attachment = AttachmentField(required=False)
			upload_session = forms.CharField(widget=HiddenInput, required=False)

			def get_model(self):
				return UploadSession

		return TestForm(data, files)

	def test_simple_upload(self):
		form = self.create_attachment_form({}, {'attachment': SimpleUploadedFile("test.txt", b"A")})
		form.process_attachments()

		self.assertTrue(form.is_valid())
		self.assertEquals(len(form.get_attachments()), 1)
		form.get_attachments()[0].delete()

	def test_no_files(self):
		form = self.create_attachment_form({})
		form.process_attachments()

		self.assertTrue(form.is_valid())
		self.assertEquals(len(form.get_attachments()), 0)

	def test_validation(self):
		with self.settings(ATTACHMENT_MAX_SIZE=1, ATTACHMENT_SIZE_FOR_CONTENT={}):
			form = self.create_attachment_form({}, {'attachment': SimpleUploadedFile("test.txt", b"AA")})
			form.process_attachments()

		self.assertFalse(form.is_valid())
		self.assertEquals(len(form.get_attachments()), 0)

	def test_delete(self):
		form = self.create_attachment_form({}, {'attachment': SimpleUploadedFile("test.txt", b"A")})
		form.process_attachments()

		formset = form.attachments
		data = {}
		data.update(self.extract_form_data(form))
		data.update(self.extract_form_data(formset.management_form))
		for attachment_form in formset:
			data.update(self.extract_form_data(attachment_form))
		data['form-0-DELETE'] = '1'

		form = self.create_attachment_form(data)
		form.process_attachments()

		self.assertTrue(form.is_valid())
		self.assertEquals(len(form.get_attachments()), 0)

	def test_move_attachment(self):
		form = self.create_attachment_form({}, {'attachment': SimpleUploadedFile("test.txt", b"A")})
		form.process_attachments()

		test_object = UploadSession()
		test_object.save()
		form.move_attachments(test_object)

		attachments = Attachment.objects.all()
		self.assertEquals(len(attachments), 1)

		attachment = attachments[0]
		attachment.delete()
