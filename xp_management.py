import datetime
import time
from google.appengine.ext import db
from google.appengine.api import memcache
import handler_base
import hashlib
import logging
import expappuser
# from google.appengine.api import app_identity
#server_url = app_identity.get_default_version_hostname()


# Important note: the outward facing "ID" numbers are stored in the public_id property
# of the ExpSession model

class ExpSession(db.Model):
    no_of_participants = db.IntegerProperty()
    time_created = db.DateTimeProperty(auto_now_add=True)
    time_closed = db.DateTimeProperty()
    questions_data = db.TextProperty()
    other_info = db.TextProperty()
    public_id = db.IntegerProperty(required=True)
    current_open = db.BooleanProperty(default=True)
    participants = db.ListProperty(item_type=long)

    def close_out(self, no_of_participants=0, questions_data="", other_info="Automatically closed."):
        if self.is_saved():
            self.no_of_participants = no_of_participants
            self.questions_data = questions_data
            self.other_info = other_info
            self.current_open = False
            self.time_closed = datetime.datetime.now()
            self.put()
            memcache.delete("current_session")

            # edit participant records
            for user in expappuser.ExpAppUser.all().filter('in_current=', True):
                user.in_current = False
                user.put()

    @classmethod
    def get_open_session(cls):
        current_session = memcache.get("current_session")
        if current_session == None:
            try:
                current_session = ExpSession.all().filter('current_open =', True).get().key().id()
                memcache.add("current_session", current_session)
            except:
                return None

        return current_session

    def add_participant(self, id_no):
        if not id_no in self.participants:
            user_to_add = expappuser.ExpAppUser.get_by_id(id_no)
            if user_to_add != None:
                self.participants.append(id_no)
                user_to_add.in_current = True
                user_to_add.put()

        self.put()

    def remove_participant(self, id_no):
        if id_no in self.participants:
            user_to_remove = expappuser.ExpAppUser.get_by_id(id_no)
            if user_to_remove != None:
                self.participants.remove(id_no)
                user_to_remove.in_current = False
                user_to_remove.put()
        self.put()


class StartNewXPHandler(handler_base.Handler):
    def get(self):
        # check for login, redirect if none
        if LoginHandler.check_login(self) == False:
            logging.info("Doing redirect to login before new XP")
            self.redirect('/login?redirect=/get-new-experiment')
            return
        else:
            # check for existing open XP (if many are open they will be closed)
            logging.info("Starting new XP...")
            old_xp_ids = []
            for open_session in ExpSession.all().filter('current_open =', True).run():
                open_session.close_out()
                old_xp_ids.append(int(open_session.public_id))
            if old_xp_ids == []:
                old_xp_ids = None
            xp_session = ExpSession(public_id=SessionCounter.get_next_id())
            xp_session.put()
            new_xp_id = xp_session.public_id
            #self.render("new_xp.html", old_xp_id=old_xp_ids, new_xp_id=new_xp_id)

            time.sleep(3)
            redirect_target = self.request.get('redirect_target', default_value="")
            if redirect_target != "":
                self.redirect(redirect_target)
            else:
                self.redirect("/")


class EndXPHandler(handler_base.Handler):
    def get(self):
        xp_id = self.request.get('i')
        if xp_id == '':
            # retrieve current XP session
            open_xp = ExpSession.all().filter('current_open =', True).get()
            if open_xp != None:
                xp_id = open_xp.public_id
            else:
                xp_id = -1
        self.render("end_xp.html", xp_id=long(xp_id))


class EndAllXPs(handler_base.Handler):
    def get(self):
        for open_session in ExpSession.all().filter('current_open =', True).run():
            open_session.close_out()


class StoreXPInfoHandler(handler_base.Handler):
    def post(self):
        logging.info("Starting XP end.")
        xp_public_id = self.request.get('xp_id')
        xp_to_store = ExpSession.all().filter('public_id =', long(xp_public_id)).get()
        if xp_to_store != None:
            xp_to_store.close_out(int(self.request.get('no_of_participants')), self.request.get('questions_data'),
                                  self.request.get('other_info'))
            time.sleep(0.1)
            self.redirect("/do-consent?id=%d" % long(xp_to_store.key().id()))

        else:
            self.redirect("/list-users?error=Error: XP " + str(xp_public_id) + " not found. Information not stored.")

        logging.info("Finishing XP end.")


class SessionCounter(db.Model):
    count = db.IntegerProperty(default=0)

    @classmethod
    def get_next_id(cls):
        # get the counter object, or create it if it doesn't exist
        the_counter = cls.get_by_key_name('the_counter')
        if the_counter == None:
            the_counter = cls(key=db.Key.from_path('SessionCounter', 'the_counter'))
            the_counter.put()

        count = the_counter.count
        the_counter.count = count + 1
        the_counter.put()
        logging.info("Counter incremented.")
        return count


class LoginHandler(handler_base.Handler):
	# these should be loaded from somewhere else
    uname = uname
    pwd = pwd
    something_else = something_else

    @classmethod
    def check_login(cls, handler_instance):
        if handler_instance.get_cookie('logged_in') == hashlib.sha256(
                                cls.uname + cls.pwd + cls.something_else).hexdigest():
            return True
        else:
            return False

    def post(self):
        if self.request.get('user') == self.uname and self.request.get('pass') == self.pwd:
            self.set_cookie('logged_in', hashlib.sha256(self.uname + self.pwd + self.something_else).hexdigest())
            redirect_target = self.request.get('redirect_target')
            if redirect_target != "":
                logging.info("Redirecting...: " + redirect_target)
                self.redirect(redirect_target)


    def get(self):
        redirect_target = self.request.get("redirect", default_value="/")
        if self.check_login(self) == True:
            logging.info("Login confirmed")
            self.redirect(redirect_target)
        else:
            logging.info("Doing manual login")
            self.response.out.write("""
	<h1>Log in:</h1>
	<form method="post">
	<input type="text" name="user"/>
	<input type="password" name="pass"/>
	<input type="hidden" name="redirect_target" value=\"""" + redirect_target + """\" />
	<input type="submit" value="login"/>
	</form>""")


class LogoutHandler(handler_base.Handler):
    def get(self):
        self.set_cookie('logged_in', '', expires=datetime.datetime.now())
        self.redirect("/login")


class DeleteParticipantConfirmHandler(handler_base.Handler):
    def get(self):
        participant_id = self.request.get("u")
        self.render("remove_user_confirm.html", participant_id=participant_id)

    def post(self):
        participant_id = self.request.get("u")

        #####
        user_to_delete = expappuser.ExpAppUser.get_by_id(long(participant_id))
        db.delete(user_to_delete)

        time.sleep(1)
        self.redirect("/list-users")


class AddUserHandler(handler_base.Handler):
    def get(self):
        xp_session = ExpSession.get_by_id(ExpSession.get_open_session())
        try:
            xp_id = xp_session.public_id
        except AttributeError:
            xp_id = None
        self.render("new_user.html", xp_session=xp_id)

    def post(self):
        user = expappuser.ExpAppUser(public_id=expappuser.ExpAppUserCounter.get_next_id())
        user.lastname = self.request.get("lastname", "")
        user.firstname = self.request.get("firstname", "")
        user_key = user.put()
        if self.request.get("add_to_session") == "yes":
            xp_session = ExpSession.get_by_id(ExpSession.get_open_session())
            xp_session.add_participant(user_key.id())
        time.sleep(0.1)
        self.redirect("/list-users")