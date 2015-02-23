import logging
import webapp2
import random
import hashlib
import time

import handler_base  # home brewed handlers
from response_report import GetResponseReportHandler
from xp_management import StartNewXPHandler, EndXPHandler, StoreXPInfoHandler, ExpSession, LoginHandler, LogoutHandler, \
    EndAllXPs, AddUserHandler, DeleteParticipantConfirmHandler
from expappuser import ExpAppUser, ListExpAppUsersHandler, ExpAppUserCounter
from participantinfoview import ParticipantInfoHandler
from consentinfoview import ConsentInfoHandler, DoConsentHandler
from userinforecord import UserInfoRecord
from email_stuff import *
from google.appengine.ext import db
import datetime
# from google.appengine.api import app_identity
# server_url = app_identity.get_default_version_hostname()


class SurveyPageHandler(handler_base.Handler):
    template_address = ""
    required_params = {}
    def validate_input(self):
        params = self.get_param_dictionary()
        # need to develop a way to ID required params.
        full_params = params.copy()

        if "" in self.required_params.values():
            return False
        return True

    def validate_participant(self,participant_id,session_id):
        """
        Check that the participant whose id is participant_id exists,
        that session session_id exists, is the active session, and
        contains participant participant_id, and retrieve or create
        the response record for this participant/session combo, return
        None if any of these conditions fails
        """
        assert(type(participant_id)==long)
        assert(type(session_id)==long)
        participant = ExpAppUser.get_by_id(long(participant_id))
        if participant is not None:
            session = ExpSession.get_open_session()
            if session == long(session_id):
                if participant_id in ExpSession.get_by_id(session).participants:
                    response_record = UserInfoRecord.all().filter('session_id = ', session_id).\
                        filter('user_id = ', participant_id).get()
                    if response_record is None:
                        response_record = participant.new_user_info_record(session_id=session_id)
                    return response_record
        return None
    
    def post(self):
        if self.validate_input() == False:
            self.redirect('/')

        participant_id = self.request.get("u")
        session_id = self.request.get("s")
        response_record = self.validate_participant(participant_id,session_id)
        if response_record is None:
            self.redirect('/participant-evaluation')
            return

        uir_id = self.get_cookie("response_record_id")
        user.store_params(full_params, long(uir_id))
        logging.info("Page 2 dump, user id %d: %s" % (user.key().id(), str(full_params)))

        # survey over, destroy user ID, response record id, and session ID cookies
        self.response.delete_cookie('user_id')
        self.response.delete_cookie('response_record_id')
        self.response.delete_cookie('response_session_id')

        self.redirect("https://docs.google.com/forms/d/1aqvMRInaCUmBBHv9Bh2F48aSaTXicMZKUv_T2--fYW0/viewform")
    
    def get(self):
        # check for active xp session, redirect if not found
        xp_session = ExpSession.get_open_session()
        if xp_session == None:
            self.redirect("/get-new-experiment")
            return

        # check that user cookie exists and matches the user we get in the arguments
        user_cookie = self.get_cookie('user_id')
        user_id = self.request.get('u')
        error_text = self.request.get('e')
        if user_id == None:
            self.redirect("/list-users")
            return
        elif user_id != user_cookie:
            raise Exception("User IDs do not match")


        try:
            user = ExpAppUser.get_by_id(long(user_id))
        except TypeError:
            self.redirect('/participant-evaluation')
            return
        self.render("user_data.html", error=error_text, lastname=user.lastname, firstname=user.firstname)


class ExperimentInfoHandler(handler_base.Handler):
    def post(self):


    def get(self):


class ParticipantEvaluationHandler(handler_base.Handler):
    """
    Handles requests for the first page of the respondent survey
    """
    def post(self):
        # validate input
        params = self.get_param_dictionary()
        # need to develop a way to ID required params.
        required_params = {}
        full_params = params.copy()

        if "" in required_params.values():
            unfilled_params = [k for k in required_params.keys() if required_params[k] == ""]
            self.render("participant_evaluation.html",
                        error=u'Please complete the following items: %s' % ( u", ".join(unfilled_params)),
                        **full_params)
            return
        # DO MORE VALIDATION HERE

        user = ExpAppUser.get_by_id(long(self.request.get("user_id")))
        if user == None:
            raise Exception("User id not found.")
        
        uir_id = self.get_cookie("response_record_id")
        logging.info(uir_id)
        user.store_params(full_params, long(uir_id))
        logging.info("Page 1 dump, user id %d: %s" % (user.key().id(), str(full_params)))
        self.redirect("/experiment-info?u=%d" % user.key().id())

    def set_userid_cookie(self, user):
        self.set_cookie("user_id", str(user.key().id()), expires=datetime.datetime.now() + datetime.timedelta(hours=3))
        
    def get_response_record(self):
        response_record_id = self.get_cookie("response_record_id")
        return UserInfoRecord.get_by_id(long(response_record_id))

#	def set_machine_cookie(self):
#		if self.get_cookie("machine_id") == None:
#			self.set_cookie("machine_id", str(random.randint(0,1000000)))

    def get(self):
        # check for active xp session, redirect if not found
        xp_session = ExpSession.get_by_id(ExpSession.get_open_session())
        logging.info("Session: %s" % xp_session.key().id())
        if xp_session == None:
            self.redirect("/")
            return
        if LoginHandler.check_login(self) == False:
            self.redirect("/login")
            return
        else:
            params = self.get_param_dictionary()
            selected_id = params.get("u", None)
            if selected_id == None:
                self.redirect("/list-users")
                return

            logging.info("Open session: " + str(xp_session.public_id))
            logging.info(selected_id)
            user = ExpAppUser.get_by_id(long(selected_id))
            self.set_userid_cookie(user)
            try:
                uir = self.get_response_record()
            except TypeError as e:
                uir = user.new_user_info_record(session_id=xp_session.key().id())

            self.set_cookie("response_record_id", str(uir.key().id()), expires=datetime.datetime.now() + datetime.timedelta(hours=3))
            self.set_cookie("response_session_id", (str(xp_session.key().id())), expires=datetime.datetime.now() + datetime.timedelta(hours=3))
            self.render("participant_evaluation.html", lastname=user.lastname,
                        firstname=user.firstname, selected_id=selected_id, response_record=uir)


class ExperimentRedirectHandler(handler_base.RedirectHandler):
    def __init__(self, *a, **kw):
        self.redirect_target = "/list-users"
        handler_base.RedirectHandler.__init__(self, *a, **kw)


class ExperimentOverHandler(handler_base.Handler):
    def get(self):
        self.render("experiment_over.html")


class FixitHandler(handler_base.Handler):
    """this handler fixes various aspects of the app datastore,
    ideally"""

    def get(self):
        for uir in UserInfoRecord.all():
            # rectify some things
            if getattr(uir, "user_id", None) == None:
                uir.user_id = -1
            else:
                uir.user_id = long(uir.user_id)
            uir.put()
            logging.info(str(uir.user_id) + ", " + str(type(uir.user_id)))
        self.redirect('/')


app = webapp2.WSGIApplication([
                                  ('/participant-evaluation', ParticipantEvaluationHandler),
                                  ('/experiment-info', ExperimentInfoHandler),
                                  ('/experiment-over', ExperimentOverHandler),
                                  ('/store-email', StoreEmailHandler),
                                  ('/remove-email', RemoveEmailHandler),
                                  ('/check-email-daily', CheckEmailDailyHandler),
                                  ('/check-email-hourly', CheckEmailHourlyHandler),
                                  ('/responses-all.tsv', GetResponseReportHandler),
                                  ('/list-users', ListExpAppUsersHandler),
                                  ('/participant-info', ParticipantInfoHandler),
                                  ('/delete-participant-confirm', DeleteParticipantConfirmHandler),
                                  ('/delete-participant', DeleteParticipantConfirmHandler),
                                  ('/do-consent', DoConsentHandler),
                                  ('/consent-info', ConsentInfoHandler),
                                  ('/get-new-experiment', StartNewXPHandler),
                                  ('/end-experiment', EndXPHandler),
                                  ('/store-session-info', StoreXPInfoHandler),
                                  ('/login', LoginHandler),
                                  ('/logout', LogoutHandler),
                                  ('/kill-sessions', EndAllXPs),
                                  ('/add-user', AddUserHandler),
                                  ('/fix-it', FixitHandler),
                                  ('/', ExperimentRedirectHandler)],
                              debug=True)

