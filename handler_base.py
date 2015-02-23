# this is copied from the Udacity web apps course

import webapp2
import jinja2
import os, sys
from google.appengine.api import memcache
import time
import logging
import datetime

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

class BadFormInput(Exception):
	pass


class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)
		
	def set_cookie(self, param, value, expires=None, domain=None):
		if expires is None:
			expires = datetime.datetime.now() + datetime.timedelta(weeks=2)
		if domain is None:
			if "localhost" not in self.request.host:
				domain = self.request.host
		logging.info(domain)
		self.response.set_cookie(param, value, expires=expires, path='/', domain=domain)
		
	def get_cookie(self, param, default_value=None, domain=None):
		return self.request.cookies.get(param, default_value)
		
	def get_last_query_time(self, id):
		cache_key = "last_query_time_%s" % id
		last_query_time = memcache.get(cache_key)
		if last_query_time != None:
			last_query_time = float(last_query_time)
		else:
			last_query_time = 0		  # could also set time here
		return last_query_time
		
	def set_last_query_time(self, id):
		cache_key = "last_query_time_%s" % id
		last_query_time = memcache.set(cache_key, time.time())
		
	def get_param_dictionary(self, *names):
		# go through the strings in names and return a dictionary containing { name:value }
		# for all the matching parameters in the request header
		request_params = {}
		if len(names) == 0:
			names = self.request.arguments()

		for name in names:
			request_params[name] = self.request.get(name)
		return request_params

		
	
	@classmethod	
	def render_str(cls, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)
		
	def render(self, template, **kw):
		self.response.headers['Content-Type']='text/html'
		self.write(self.render_str(template, **kw))

		
		
class RedirectHandler(webapp2.RequestHandler):
	class RedirectError(Exception):
		pass
		
	def __init__(self, *a, **kw):
		try:
			self.redirect_target		# if it doesn't exist, it will raise a NameError
		except NameError:	 
			self.redirect_target = None
		
		webapp2.RequestHandler.__init__(self,*a,**kw)
		
	def get(self):
		if self.redirect_target:
			self.redirect(self.redirect_target)
		else:
			self.error(404)
			raise RedirectError("Redirect not set")
			
class Error404Handler(webapp2.RequestHandler):
	def get(self):
		self.response.set_status(404)
		self.response.out.write('Nope! (404)')	  
 
			
