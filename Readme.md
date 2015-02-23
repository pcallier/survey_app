## Talk Lab Dashboard and Survey App
### Patrick Callier
### 2014

This is a Google App Engine app that serves up a survey that is mostly defined in a 
set of Jinja2 templates in the templates directory. There is some hardcoding and other 
workarounds in the code, but any named field in a survey form will be saved to a
record in the Datastore. There is an interface for adding participants, sending them 
reminders about lab appointments, and outputting the survey results as a flat TSV table.

It uses a lot of "Handler" boilerplate from Udacity's Web Programming course to wrap
HTTP requests.