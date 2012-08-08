from google.appengine.ext import webapp
from google.appengine.api.mail import EmailMessage
from scripts.main import BaseHandler
from scripts.gaesessions import get_current_session
from scripts.gaesettings import gaesettings
from scripts.database_models.housingapplication import HousingApplication
from wtforms.ext.appengine.db import model_form

class Housing_BaseHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
      BaseHandler.__init__(self, *args, **kwargs)
      self.template_vars = {
        'HousingSelected':"top-level-dropdown-selected",
      }

class CchHandler(Housing_BaseHandler):
    def get(self):
        self.render_template("housing/cch.html", self.template_vars)

class WcchHandler(Housing_BaseHandler):
    def get(self):
        self.render_template("housing/wcch.html", self.template_vars)

class ApplicationHandler(Housing_BaseHandler):
    FormClass = model_form(HousingApplication)

    def get(self):
        session = get_current_session()
        if self.request.get('done'):
          self.template_vars['app_name'] = session.get("app-name")
          self.render_template("housing/application_completion.html", self.template_vars, use_cache=False)
        else:
          if self.request.get('retry'):
            form = self.FormClass(formdata=session.get('housing_application'))
            if session.has_key('housing_application'):
              form.validate()
          else:
            form = self.FormClass()
            house = self.request.get('house')
            if house == 'cch':
              form.House.data = "Men's Christian Campus House"
            elif house == 'wcch':
              form.House.data = "Women's Christian Campus House"

          self.template_vars['form'] = form
          self.render_template("housing/application.html", self.template_vars, use_cache=False)

    def post(self):
        session = get_current_session()
        form = self.FormClass(self.request.POST)
        if form.validate():
          if 'housing_application' in session:
            del session['housing_application']
          filled_housing_application = HousingApplication(**form.data)
          filled_housing_application.put()

          # send email
          message = EmailMessage()
          if form.House.data == "Men's Christian Campus House":
            message.sender = "CCH Housing Application <admin@rollaccf.org>"
            message.to = gaesettings.HousingApplicationCch_CompletionEmail
            message.subject = "CCH Housing Application (%s)" % form.FullName.data
          else:
            message.sender = "WCCH Housing Application <admin@rollaccf.org>"
            message.to = gaesettings.HousingApplicationWcch_CompletionEmail
            message.subject = "WCCH Housing Application (%s)" % form.FullName.data
          message.html = filled_housing_application.generateHtmlMailMessageBody();
          message.body = filled_housing_application.generatePlainTextMailMessageBody();
          message.send()

          session["app-name"] = filled_housing_application.FullName
          self.redirect(self.request.path + "?done=1")
        else:
          session['housing_application'] = self.request.POST
          self.redirect(self.request.path + '?retry=1')

class InfoHandler(Housing_BaseHandler):
    def get(self):
        self.render_template("housing/info.html", self.template_vars)


application = webapp.WSGIApplication([
  ('/housing/info.*', InfoHandler),
  ('/housing/cch.*', CchHandler),
  ('/housing/wcch.*', WcchHandler),
  ('/housing/application.*', ApplicationHandler),
  ], debug=BaseHandler.debug)
