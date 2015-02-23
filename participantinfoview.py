import random, logging, time
import webapp2, jinja2
import userinforecord
from expappuser import ExpAppUser
from userinforecord import UserInfoRecord

from google.appengine.ext import db

import handler_base

class ParticipantInfoHandler(handler_base.Handler):
	def get(self):
		user_id = long(self.get_param_dictionary().get('u',"-1"))
		if user_id != "-1":
			user_info_records = db.GqlQuery('SELECT * FROM UserInfoRecord WHERE user_id = %d' % user_id).run()
			user = ExpAppUser.get_by_id(user_id)
			logging.debug(user_id)
			self.render("participant_info.html", participant_no=user.public_id, participant_id = user_id, userinforecords=[(record.key().id(), record.time_of_response, record.user_id) for record in user_info_records])