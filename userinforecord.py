import random, logging
import webapp2, jinja2

from google.appengine.ext import db

import handler_base
import xp_management
import date_stuff
import datetime

class UserInfoRecord(db.Expando):
	time_of_response = db.DateTimeProperty(auto_now_add=True)
	session_id = db.IntegerProperty(required=True)
	user_id = db.IntegerProperty(required=True)
	consent_date = db.DateProperty()
	
	def response_report(self):
		# return a tab-delimited one-line string with all the survey responses for this user in it
		# get xp session info
		if getattr(self, "session_id", None) == None:
			logging.info("returning blank record")
			return ""
		xp_session = xp_management.ExpSession.get_by_id(self.session_id)
		xp_session_id = xp_session.public_id
		
		try:
			time_created = date_stuff.do_dst(getattr(xp_session, "time_created", None) + date_stuff.utc_offset)
		except TypeError:
			time_created = datetime.datetime(year=1970,month=1,day=1)
		try:
			time_closed = date_stuff.do_dst(getattr(xp_session, "time_closed", None) + date_stuff.utc_offset)
		except TypeError:
			time_closed = datetime.datetime(year=1970,month=1,day=1)
		try:
			time_of_response = date_stuff.do_dst(self.time_of_response + (date_stuff.utc_offset))
		except TypeError:
			time_of_response = datetime.datetime(year=1970,month=1,day=1)
		report_items = [xp_session_id,xp_session.key().id(),
			time_created.strftime("%Y-%m-%d %H:%m"),time_closed.strftime("%Y-%m-%d %H:%m"),
			getattr(xp_session, "no_of_participants", ""),
			getattr(xp_session, "question_data", ""),getattr(xp_session, "other_info", ""),
			getattr(self, "relationship", ""),getattr(self, "relationship_more", ""),getattr(self, "interlocutor_age", ""),
			getattr(self, "interlocutor_gender", ""),getattr(self, "interlocutor_race", ""),
			getattr(self, "interlocutor_sexual_orientation", ""),getattr(self, "enjoyed_self", ""),
			getattr(self, "interlocutor_enjoyed", ""),getattr(self, "felt_comfortable_self", ""),
			getattr(self, "interlocutor_felt_comfortable", ""),getattr(self, "we_clicked", ""),
			getattr(self, "hang_out_group", ""),getattr(self, "hang_out_alone", ""),
			getattr(self, "go_on_a_date", ""),getattr(self, "set_them_up", ""),
			getattr(self, "more_comments", ""),getattr(self, "age", ""),getattr(self, "gender", ""),
			getattr(self, "race", ""),getattr(self, "sexual_orientation", ""),
			getattr(self, "attended_highschool", ""),getattr(self, "highschool", ""),
			getattr(self, "finished_highschool", ""),getattr(self, "attended_twoyear", ""),
			getattr(self, "twoyear", ""),getattr(self, "finished_twoyear", ""),
			getattr(self, "attended_fouryear", ""),getattr(self, "fouryear", ""),
			getattr(self, "finished_fouryear", ""),getattr(self, "attended_professional", ""),
			getattr(self, "professional", ""),getattr(self, "finished_professional", ""),
			getattr(self, "attended_masters", ""),getattr(self, "masters", ""),getattr(self, "finished_masters", ""),
			getattr(self, "attended_doctoral", ""),getattr(self, "doctoral", ""),getattr(self, "finished_doctoral", ""),
			getattr(self, "other_education", ""),getattr(self, "profession", ""),getattr(self, "placelived_1", ""),
			getattr(self, "whenlived_1", ""),getattr(self, "placelived_2", ""),getattr(self, "whenlived_2", ""),
			getattr(self, "placelived_3", ""),getattr(self, "whenlived_3", ""),getattr(self, "placelived_4", ""),
			getattr(self, "whenlived_4", ""),getattr(self, "placelived_5", ""),getattr(self, "whenlived_5", ""),
			getattr(self, "placelived_6", ""),getattr(self,"whenlived_6",""),str(self.key().id()),
			time_of_response.strftime("%Y-%m-%d %H:%m"),getattr(self, "where_sat", "unknown")]
		
		response_report = '\t'.join([unicode(x).replace('\t','') for x in report_items])
		logging.info(response_report.replace("\n","***"))
		return response_report
