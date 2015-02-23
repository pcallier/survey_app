import random, logging, time
import webapp2, jinja2
import userinforecord

from google.appengine.ext import db

import handler_base
import xp_management


class ExpAppUserCounter(db.Model):
    count = db.IntegerProperty(default=0)

    @classmethod
    def get_next_id(cls):
        # get the counter object, or create it if it doesn't exist
        the_counter = cls.get_by_key_name('the_counter')
        if the_counter == None:
            the_counter = cls(key=db.Key.from_path('ExpAppUserCounter', 'the_counter'))
            the_counter.put()

        count = the_counter.count
        the_counter.count = count + 1
        the_counter.put()
        logging.info("Counter incremented.")
        return count


class ExpAppUser(db.Expando):
    date_created = db.DateTimeProperty(auto_now_add=True)
    public_id = db.IntegerProperty(required=True)
    user_info_records = db.ListProperty(item_type=long)  # list of id's of UserInfoRecords, holding
    # data from responses
    current_response = db.IntegerProperty(default=None)
    in_current = db.BooleanProperty(default=False)

    @classmethod
    def users_table(cls, with_buttons=None):
        """ return an html chunk with a table that lists
            all current users (i.e. participants), their names, and their
            user ids.

            with_buttons: a string with the URL target which should accept a parameter i to
                            add the user with that ID to the current interaction
        """
        to_render = "Users table:<br /><table><tr><td>User ID</td><td>Last name</td><td>First name</td>"
        if with_buttons != None:
            to_render = to_render + "<td>In XP?</td>"
        to_render = to_render + "</tr>"

        cur_session = xp_management.ExpSession.get_by_id(xp_management.ExpSession.get_open_session())
        for user_rec in cls.all():
            to_render = to_render + "<tr><td>" + str(user_rec.public_id) + "</td><td>" + getattr(user_rec, "lastname",
                                                                                                 "") + "</td><td>" + getattr(
                user_rec, "firstname", "") + "</td>"
            if with_buttons != None and cur_session != None:
                user_id = user_rec.key().id()
                if user_id not in cur_session.participants:
                    to_render = to_render + "<td><a href=\"" + with_buttons + "?i=" + str(user_id) + "\">add</a></td>"
                else:
                    to_render = to_render + "<td>yes <a href=\"" + with_buttons + "?remove=" + str(
                        user_id) + "\">remove</a></td>"
            to_render = to_render + "</tr>"
        to_render = to_render + "</table>"
        return to_render

    def response_report(self):
        responses = []
        logging.info("Generating response report for user %s %s" % (self.firstname, self.lastname))
        for info_record_id in self.user_info_records:
            logging.info("Retreiving response report for record %d" % (info_record_id))
            responses.append('\t'.join([getattr(self, "lastname", ""), getattr(self, "firstname", ""),
                                        str(self.public_id), str(self.key().id()),
                                        userinforecord.UserInfoRecord.get_by_id(
                                            info_record_id).response_report()]).replace("\r", " "))
        return responses

    def new_user_info_record(self, session_id=None):
        logging.info("My session id: %s" % session_id)
        info_record = userinforecord.UserInfoRecord(session_id=session_id,user_id=self.key().id())
        info_record_key = info_record.put()
        self.user_info_records.append(info_record_key.id())
        self.put()
        return info_record

    def store_params(self, params, uir_id=None):
        cur_xp_session = xp_management.ExpSession.get_open_session()
        if self.current_response == None and uir_id == None:
            raise Exception("No current response record open and none supplied")
        else:
            if uir_id == None:
                info_record = userinforecord.UserInfoRecord.get_by_id(self.current_response)
            else:
                info_record = userinforecord.UserInfoRecord.get_by_id(uir_id)
            if info_record.session_id != cur_xp_session.key().id():
                raise Exception("Response record session ID (%d) does not match current session (%d)" % (info_record.session_id, cur_xp_session))

        for name, value in params.iteritems():
            # we used to worry about overwriting old values, but I
            # think we need to get over that.
            setattr(info_record, name, value)

        info_record.put()

    @classmethod
    def response_report_header(cls):
        logging.info("Writing header")
        # return a string with the tab-separated header for a tsv file response report
        return "lastname\tfirstname\t" + \
               "user_id\tinternal_user_id\t" + \
               "session_id\tinternal_session_id\tsession_start\tsession_end\t" + \
               "no_of_participants\tquestion_data\tother_info\t" + \
               "relationship\trelationship_more\t" + \
               "interlocutor_age\tinterlocutor_gender\tinterlocutor_race\t" + \
               "interlocutor_sexual_orientation\tenjoyed_self\tinterlocutor_enjoyed\t" + \
               "felt_comfortable_self\tinterlocutor_felt_comfortable\twe_clicked\t" + \
               "hang_out_group\thang_out_alone\tgo_on_a_date\tset_them_up\tmore_comments\t" + \
               "age\tgender\trace\tsexual_orientation\tattended_highschool\t" + \
               "highschool\tfinished_highschool\tattended_twoyear\ttwoyear\t" + \
               "finished_twoyear\tattended_fouryear\tfouryear\tfinished_fouryear\t" + \
               "attended_professional\tprofessional\tfinished_professional\t" + \
               "attended_masters\tmasters\tfinished_masters\t" + \
               "attended_doctoral\tdoctoral\tfinished_doctoral\t" + \
               "other_education\tprofession\t" + \
               "placelived_1\twhenlived_1\tplacelived_2\twhenlived_2\tplacelived_3\twhenlived_3\t" + \
               "placelived_4\twhenlived_4\tplacelived_5\twhenlived_5\tplacelived_6\twhenlived_6\t" + \
               "userinforecord_id\tuserinforecord_timestamp\twhere_sat"


class ListExpAppUsersHandler(handler_base.Handler):
    def get(self):
        if xp_management.LoginHandler.check_login(self) is not True:
            self.redirect("/login?redirect=/list-users")
            return
        open_session =  xp_management.ExpSession.get_by_id(xp_management.ExpSession.get_open_session())
        user_id = self.request.get("i")
        if user_id != "":
            if open_session != None:
                open_session.add_participant(long(user_id))
                time.sleep(0.1)
                self.redirect("/list-users")
                return
            else:
                self.write("<div color=\"red\">User " + str(
                    user_id) + " not found, or perhaps you do not have an experiment running?.</div>")
        remove_id = self.request.get("remove")
        if remove_id != "":
            if open_session != None:
                open_session.remove_participant(long(remove_id))
                time.sleep(0.1)
                self.redirect("/list-users")
                return

        errortext = self.request.get("error")
        user_info = []
        if open_session != None:
            xp_id = open_session.public_id
            xp_session_datetime = open_session.time_created
            participants = open_session.participants
        else:
            xp_id = None
            xp_session_datetime = None
            participants = []

        logging.info("Writing users")
        for user_rec in ExpAppUser.all().order('-in_current').order('-public_id'):
            user_info.append((getattr(user_rec, "public_id", ""), getattr(user_rec, "lastname", ""),
                              getattr(user_rec, "firstname", ""), user_rec.key().id()))
        self.render("xp_management.html", user_info=user_info,
                    xp_participants=participants, redirect_url="/list-users", error=errortext,
                    xp_session=xp_id, xp_session_datetime=xp_session_datetime)