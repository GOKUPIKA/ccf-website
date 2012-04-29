import os
from google.appengine.api import images, memcache, capabilities
from google.appengine.ext import webapp
from google.appengine.ext.db import GqlQuery
from scripts.main import BaseHandler
from scripts.gaesessions import get_current_session
from scripts.gaesettings import gaesettings
from scripts.database_models import HomepageSlide
from wtforms.ext.appengine.db import model_form

class ManageHomePageSlidesHandler(BaseHandler):
    def get(self):
      # reorder slides if need be
      direction = self.request.get("direction")
      displayOrderToMove = self.request.get("displayOrder")
      if direction != '' and displayOrderToMove != '':
        displayOrderToMove = int(displayOrderToMove)
        # I am assuming displayOrder has no duplicates
        FirstObject = GqlQuery("SELECT * FROM HomepageSlide WHERE DisplayOrder = :1", displayOrderToMove).get()
        if direction == 'up':
          SecondObject = GqlQuery("SELECT * FROM HomepageSlide WHERE DisplayOrder < :1 ORDER BY DisplayOrder DESC", displayOrderToMove).get()
        else:
          SecondObject = GqlQuery("SELECT * FROM HomepageSlide WHERE DisplayOrder > :1 ORDER BY DisplayOrder ASC", displayOrderToMove).get()

        FirstObject.DisplayOrder, SecondObject.DisplayOrder = SecondObject.DisplayOrder, FirstObject.DisplayOrder
        FirstObject.put()
        SecondObject.put()

      # get slides for the tab we are on
      # TODO: add paging
      tab = self.request.get("tab", default_value='onhomepage')
      if tab == "disabled":
        slides = GqlQuery("SELECT * FROM HomepageSlide WHERE Enabled = False").fetch(20);
      elif tab == "enabled":
        slides = GqlQuery("SELECT * FROM HomepageSlide WHERE Enabled = True").fetch(20);
        for slide in slides:
          if slide.DisplayOrder: # it's on the Homepage
            slides.remove(slide)
      else:
        slides = GqlQuery("SELECT * FROM HomepageSlide WHERE DisplayOrder > 0").fetch(20);

      self.render_template("manage/homepage_slides/homepage_slides.html",
      { 'title':"Homepage Slides",
        'slides':slides,
        'tab':tab,
      })

class ManageNewSlideHandler(BaseHandler):
    FormClass = model_form(HomepageSlide)

    def get(self):
      if not capabilities.CapabilitySet('datastore_v3, write').is_enabled():
        self.fatal_error(
          "500 Internal Server Error",
          """The datastore is down. Please try again in a few minutes.
             If this continues to happen, please contact webmaster@rollaccf.org"""
        )
        return

      session = get_current_session()

      if self.request.get('retry'):
        form = self.FormClass(formdata=session.get('new_slide'))
        if session.has_key('new_slide'):
          form.validate()
      elif self.request.get('edit'):
        editKey = self.request.get("edit")
        form = self.FormClass(obj=HomepageSlide.get(editKey))
      else:
        form = self.FormClass()

      self.render_template("manage/homepage_slides/new_slide.html",
      { 'title':"New Homepage Slide",
        'MaxHomepageSlides':gaesettings.MaxHomepageSlides,
        'LinkPrefix':'/'.join((os.environ['HTTP_HOST'],)),
        'editKey':self.request.get('edit'),
        'form':form,
      })

    def post(self):
      # TODO: add cgi escape
      # TODO: add error checking
      session = get_current_session()
      form = self.FormClass(self.request.POST)
      editKey = self.request.get("edit")
      if form.validate(): #add validators, aka If url needs page title and html
        if 'new_slide' in session:
          del session['new_slide']
        if editKey:
          filled_homepage_slide = HomepageSlide.get(editKey)
          if filled_homepage_slide != None:
            filled_homepage_slide.Update(form.data)
          else:
            self.fatal_error("500", "The slide you are trying to edit does not exist")
            return
        else:
          filled_homepage_slide = HomepageSlide()
          filled_homepage_slide.Update(form.data)

        if self.request.get("onHomepage") and filled_homepage_slide.Enabled:
          displayOrderObject = GqlQuery("SELECT * FROM HomepageSlide ORDER BY DisplayOrder DESC").get()
          filled_homepage_slide.DisplayOrder = displayOrderObject.DisplayOrder + 1 if displayOrderObject else 1
        else:
          filled_homepage_slide.DisplayOrder = None

        if filled_homepage_slide.Image:
          filled_homepage_slide.Image=images.resize(filled_homepage_slide.Image, 600, 450)

        filled_homepage_slide.put()
        memcache.delete("homepageSlides")
        self.redirect("/manage/homepage_slides")
      else:
        session['new_slide'] = self.request.POST
        self.redirect(self.request.path + '?edit=%s&retry=1' % editKey)


application = webapp.WSGIApplication([
  ('/manage/homepage_slides/new_slide.*', ManageNewSlideHandler),
  ('/manage/homepage_slides.*', ManageHomePageSlidesHandler),
  ], debug=True)
