import os
from os.path import join
from google.appengine.api import images, memcache
from google.appengine.ext import webapp
from google.appengine.ext.db import GqlQuery, to_dict
from scripts.main import BaseHandler
from scripts.gaesettings import gaesettings
from scripts.database_models import HomepageSlide

class ManageHomePageSlidesHandler(BaseHandler):
    def get(self):
      # TODO: add paging
      slides = GqlQuery("SELECT * FROM HomepageSlide").fetch(20);
      slideDicts = []
      for slide in slides:
        d = to_dict(slide)
        d['key'] = slide.key()
        slideDicts.append(d)

      self.render_template(join("manage", "homepage_slides", "homepage_slides.html"), { 'title':"Homepage Slides", 'slides':slideDicts, })

class ManageNewSlideHandler(BaseHandler):
    def get(self):
      # TODO: add Capabilities API to check that the datastore is up
      # TODO: add image handling for editing
      editKey = self.request.get("edit")
      slideValues = None
      if editKey != '':
        editDbSlide = HomepageSlide.get(editKey)
        if editDbSlide != None:
          slideValues = to_dict(editDbSlide)
          slideValues['key'] = editDbSlide.key()

      self.render_template(join("manage", "homepage_slides", "new_slide.html"),
        { 'title':"New Homepage Slide",
          'MaxHomepageSlides':gaesettings.MaxHomepageSlides,
          'LinkPrefix':'/'.join((os.environ['HTTP_HOST'], gaesettings.HomepageLinkPrefix)),
          'slideValues':slideValues,
      })
    def post(self):
      # TODO: add cgi escape
      # TODO: add error checking and fatel errors
      enabled = self.request.get("enabled")
      slideImage = images.resize(self.request.get("image"), 600, 450)
      link = self.request.get("link")
      title = self.request.get("title")
      html = self.request.get("slideHtml")

      editKey = self.request.get("edit")
      if editKey != '':
        editDbSlide = HomepageSlide.get(editKey)
        if editDbSlide != None:
          editDbSlide.Enabled=bool(enabled)
          editDbSlide.Link=link
          editDbSlide.Image=slideImage
          editDbSlide.Title=title
          editDbSlide.Html=html
          editDbSlide.put()
      else:
        newSlide = HomepageSlide(Enabled=bool(enabled), Link=link, Image=slideImage, Title=title, Html=html)
        newSlide.put()

      if enabled:
        memcache.delete("homepageSlides")
      self.redirect(self.request.path)

application = webapp.WSGIApplication([
  ('/manage/homepage_slides/new_slide.*', ManageNewSlideHandler),
  ('/manage/homepage_slides.*', ManageHomePageSlidesHandler),
  ], debug=True)
