import os
from google.appengine.api import images, memcache, capabilities
from google.appengine.ext import webapp
from google.appengine.ext.db import GqlQuery
from scripts.main import BaseHandler
from scripts.gaesettings import gaesettings
from scripts.database_models import HomepageSlide

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
    def get(self):
      if not capabilities.CapabilitySet('datastore_v3, write').is_enabled():
        self.fatal_error(
          "500 Internal Server Error",
          """The datastore is down. Please try again in a few minutes.
             If this continues to happen, please contact webmaster@rollaccf.org"""
        )
        return
      editKey = self.request.get("edit")
      editDbSlide = None
      if editKey != '':
        editDbSlide = HomepageSlide.get(editKey)

      self.render_template("manage/homepage_slides/new_slide.html",
      { 'title':"New Homepage Slide",
        'MaxHomepageSlides':gaesettings.MaxHomepageSlides,
        'LinkPrefix':'/'.join((os.environ['HTTP_HOST'],)),
        'slideValues':editDbSlide,
      })
    def post(self):
      # TODO: add cgi escape
      # TODO: add error checking and fatal errors
      enabled = bool(self.request.get("enabled"))
      slideImage = self.request.get("image")
      link = self.request.get("link")
      title = self.request.get("title")
      html = self.request.get("slideHtml")
      onHomepage = self.request.get("onHomepage")

      newSlide = None
      editKey = self.request.get("edit")
      if editKey != '':
        editDbSlide = HomepageSlide.get(editKey)
        if editDbSlide != None:
          newSlide = editDbSlide
      if newSlide == None:
        newSlide = HomepageSlide()

      newSlide.Enabled=enabled
      if onHomepage and enabled:
        displayOrderObject = GqlQuery("SELECT * FROM HomepageSlide ORDER BY DisplayOrder DESC").get()
        newSlide.DisplayOrder = displayOrderObject.DisplayOrder + 1 if displayOrderObject else 1
      else:
        newSlide.DisplayOrder = None
      newSlide.Link=link
      if slideImage:
        newSlide.Image=images.resize(slideImage, 600, 450)
      newSlide.Title=title
      newSlide.Html=html
      newSlide.put()

      memcache.delete("homepageSlides")
      self.redirect(self.request.path)

application = webapp.WSGIApplication([
  ('/manage/homepage_slides/new_slide.*', ManageNewSlideHandler),
  ('/manage/homepage_slides.*', ManageHomePageSlidesHandler),
  ], debug=True)
