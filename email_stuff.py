#!/usr/bin/env python

from google.appengine.ext import db
import handler_base
import xp_management
from google.appengine.api import mail
import re
import logging
import datetime
import date_stuff

class EmailAddress(db.Model):
	email_address = db.StringProperty(required=True)
	appt_datetime = db.DateTimeProperty(required=True)
	
	def send_reminder(self, subject="Talk Lab reminder",body=""):
		if body == "":
			body = """Hello there,
			
This email is a reminder that you have signed up to come into the Interactional Sociophonetics 
Lab (the Talk Lab) at %s. The lab is located in Margaret Jacks Hall, Building 460, room 021.

Please be prompt. We look forward to seeing you!

Best,
Patrick Callier (on behalf of the Lab)

P.S. If you need to cancel or reschedule, please contact us immediately.
P.P.S. To stop receiving email reminders, please visit http://talklab-survey.appspot.com/remove-email=%s
""" % (self.appt_datetime.strftime("%I:%M %p, %A %B %d"), self.email_address)
		mail.send_mail("stanfordtalklab@gmail.com",self.email_address,subject,body)
			
	
class StoreEmailHandler(handler_base.Handler):
	def get(self):
		error = self.request.get("error")
		if xp_management.LoginHandler.check_login(self):
			self.render("get_email.html", error=error)
		else:
			self.redirect("/login?redirect=/store-email")

	def post(self):
		if xp_management.LoginHandler.check_login(self):
			logging.info("Processing email submission")
			email_address = self.request.get('email_address')
			appt_date = self.request.get('appt_date')
			appt_time = self.request.get('appt_time')
			
			logging.info(",".join([email_address,appt_date,appt_time]))
			error = ""
			if re.search(r".*@.*\..*",email_address) == None:
				error = error + "Please enter a valid email address. "
			else:
				logging.info(email_address + " is all right!")
			if re.search(r"\d{4}-\d{2}-\d{2}",appt_date) == None:
				error = error + "Please enter a date in the yyyy-mm-dd format. "
			if re.search(r"\d{2}:\d{2}",appt_time) == None:
				error = error + "Please enter a time in 24-hr hh:mm format. "
			
			logging.info(error)
			if error != "":
				logging.info("Redirecting to " + "/store-email?error=%s"%error)
				self.redirect("/store-email?error=%s"%error)
				return
			else:
				logging.info("Not redirecting")
			
			address_record = EmailAddress(email_address=email_address,
				appt_datetime=datetime.datetime.strptime(' '.join([appt_date, appt_time]), "%Y-%m-%d %H:%M"))
			address_record.put()
			self.redirect("/list-users")
		else:
			logging.info("Not logged in, redirecting to /store-email")
			self.redirect("/store-email")
			
class RemoveEmailHandler(handler_base.Handler):
	def get(self):
		email = self.request.get("email")
		for email_record in EmailAddress.all().filter('email_address = ', email):
			email_record.delete()
		self.render("remove_email.html",email_address=email)
		
class CheckEmailHourlyHandler(handler_base.Handler):
	def get(self):
		# do 1-hr out notice
		now = date_stuff.do_dst(datetime.datetime.now() + date_stuff.utc_offset)
		for email_rec in EmailAddress.all().filter('appt_datetime >', now).filter(
			'appt_datetime <=', now + datetime.timedelta(hours=1,minutes=20)):
			email_rec.send_reminder()

class CheckEmailDailyHandler(handler_base.Handler):
	def get(self):
		# do 24-hr out notice
		now = date_stuff.do_dst(datetime.datetime.now() + date_stuff.utc_offset)
		for email_rec in EmailAddress.all().filter('appt_datetime >', now).filter(
			'appt_datetime <=', now + datetime.timedelta(hours=24)):
			email_rec.send_reminder()
		