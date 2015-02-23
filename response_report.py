import random, logging
import re
import webapp2, jinja2

from google.appengine.ext import db

import handler_base
from expappuser import ExpAppUser

class GetResponseReportHandler(handler_base.Handler):
    def post(self):
		self.write_report()
            
            
    def get(self):
        self.response.out.write("""<h1>Log in:</h1>
<form method="post">
<input type="text" name="user"/>
<input type="password" name="pass"/>
<input type="submit" value="login"/>
</form>""")
    
    def write_report(self):
    	logging.info("Writing TSV")
        self.response.headers['Content-Type']='text/csv'
        # write headers
        # get users 
        user_records = ExpAppUser.all()
        response_table = \
        '\n'.join([ExpAppUser.response_report_header(),
        	'\n'.join(
        			[re.sub("\n", " ", user_record_entry) for user_record in user_records for user_record_entry in user_record.response_report()]
        		)])
        self.response.out.write(response_table)
    