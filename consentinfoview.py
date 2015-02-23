import random, logging, time
import webapp2, jinja2
import userinforecord
import expappuser
import xp_management
import datetime,time

from google.appengine.ext import db

import handler_base

class ConsentInfoHandler(handler_base.Handler):
	def get(self):
		logging.info("GET")
		params = self.get_param_dictionary()
		user_info_record_id = long(params.get('uir',"-1"))
		if user_info_record_id != "-1":
			user_info_record = userinforecord.UserInfoRecord.get_by_id(user_info_record_id)
			participant_object=expappuser.ExpAppUser.get_by_id(long(getattr(user_info_record,"user_id",-1)))
			self.render("consent_info.html",
			uir_id=user_info_record_id,
			loop=params.get('loop',0),
			session_id=params.get('session_id','-1'),
			participant_no=	participant_object.public_id,
			participant_name = "%s, %s" % (participant_object.lastname, participant_object.firstname),
			consent_signature=	getattr(user_info_record, "consent_signature", False),
			consent_date=		getattr(user_info_record, "consent_date", "0000-00-00"),
			consent_taping=	getattr(user_info_record, "consent_taping", False),
			consent_identity=	getattr(user_info_record, "consent_identity", False),
			consent_conferences=	getattr(user_info_record, "consent_conferences", False),
			consent_experiments=	getattr(user_info_record, "consent_experiments", False),
			consent_stanford=	getattr(user_info_record, "consent_stanford", False),
			consent_outside=	getattr(user_info_record, "consent_outside", False),
			consent_followup=	getattr(user_info_record, "consent_followup", False))
			
	def post(self):
		logging.info("POST")
		params = self.get_param_dictionary()
		uir_id = long(params.get('uir_id',"-1"))
		uir = userinforecord.UserInfoRecord.get_by_id(uir_id)
		
		uir.consent_signature = params.get('consent_signature',False)!=False
		uir.consent_date=		datetime.date(*time.strptime(params.get('consent_date',"0000-00-00"), "%Y-%m-%d")[0:3])
		uir.consent_taping=		params.get('consent_taping',False)!=False
		uir.consent_identity=	params.get('consent_identity',False)!=False
		uir.consent_conferences=	params.get('consent_conferences',False)!=False
		uir.consent_experiments=	params.get('consent_experiments',False)!=False
		uir.consent_stanford=	params.get('consent_stanford',False)!=False
		uir.consent_outside=	params.get('consent_outside',False)!=False
		uir.consent_followup=	params.get('consent_followup',False)!=False
		
		uir.put()
		time.sleep(1)
		
		loop = long(params.get('loop'))
		session_id = long(params.get('session_id'))
		logging.info(loop)
		logging.info(session_id)
		if loop == 1:
			self.redirect("/do-consent?id=%d" % session_id)
			return
		self.redirect("/participant-info?u=%s" % uir.user_id)

class DoConsentHandler(handler_base.Handler):
	def get(self):
		# get session id
		params = self.get_param_dictionary()
		if params.get("id", None) == None:
			self.redirect("/?error=No session ID specified for consent information input")
		else:
			id=long(params.get('id'))
		# find active users who don't have consent information for responses in this session
		active_user_ids = xp_management.ExpSession.get_by_id(id).participants
		
		for active_user_id in active_user_ids:
			uir_to_check = None
			active_user = expappuser.ExpAppUser.get_by_id(active_user_id)
			# gather info records for this user, this session
			this_session_uirs = userinforecord.UserInfoRecord.all().filter('user_id =', active_user.key().id()).filter('session_id =', id).fetch(10)
			
			if len(this_session_uirs) == 0:
				# make a new blank info record for user without survey response
				new_uir = active_user.new_user_info_record(session_id=id)
				new_uir.user_id = long(active_user.key().id())
				new_uir.put()
				uir_to_check = new_uir
				
			else:
				for uir in this_session_uirs:
					if uir.consent_date == None and uir.session_id:
						uir_to_check = uir
						break
			
			if uir_to_check != None:	
				self.redirect("/consent-info?uir=%d&session_id=%d&loop=1" % (uir_to_check.key().id(), id))
				return
		self.redirect("/")