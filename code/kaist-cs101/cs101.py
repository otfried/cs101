# --------------------------------------------------------------------

from cgi import escape

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

# --------------------------------------------------------------------

class MainPage(webapp.RequestHandler):
  def get(self):
    # Write the submission form
    out = self.response.out
    out.write('<html><body>')
    out.write('<form action="/result" method="post">\n')
    out.write("""
     <h2>KAIST CS101</h2>
     <div>What is your name? <input name="name"/></div>
     <div>What is your favorite number? <input name="number"/></div>
     <div><input type="submit" value="Submit"></div>
     </form></body></html>""")
    
class Result(webapp.RequestHandler):
  def post(self):
    out = self.response.out
    name = self.request.get('name')
    nums = self.request.get('number')
    num = int(nums)
    sqnum = num ** 2
    out.write('<html><body>')
    out.write('<p>Hello %s,</p>' % name)
    out.write("<p>Your lucky square is %d.</p>" % sqnum)
    out.write('</body></html>\n')
    
# --------------------------------------------------------------------

application = webapp.WSGIApplication([('/', MainPage),
                                      ('/result', Result)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()

# --------------------------------------------------------------------
