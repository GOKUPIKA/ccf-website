from google.appengine.ext import webapp
from scripts.main import BaseHandler
from scripts.database_models import HousingApplication
from wtforms.ext.appengine.db import model_form

class CchHandler(BaseHandler):
    def get(self):
        self.render_template("housing/cch.html",
        { 'title':"Christian Campus Fellowship Men's Housing Info",
          'headerText':"CCH Housing Information",
          'HousingSelected':"top-level-dropdown-selected",
        })

class WcchHandler(BaseHandler):
    def get(self):
        self.render_template("housing/wcch.html",
        { 'title':"Christian Campus Fellowship Women's Housing Info",
          'headerText':"WCCH Housing Information",
          'HousingSelected':"top-level-dropdown-selected",
        })

class ApplicationHandler(BaseHandler):
    def get(self):
        FormClass = model_form(HousingApplication)
        form = FormClass()
        self.render_template("housing/application.html",
        { 'title':"Christian Campus Fellowship Housing Application",
          'headerText':"Housing Application",
          'HousingSelected':"top-level-dropdown-selected",
          'form':form,
        })


application = webapp.WSGIApplication([
  ('/housing/cch.*', CchHandler),
  ('/housing/wcch.*', WcchHandler),
  ('/housing/application.*', ApplicationHandler),
  ], debug=True)
