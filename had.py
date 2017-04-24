import os
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.wsgi import SharedDataMiddleware
from werkzeug.utils import redirect
import requests
import datetime
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
from jinja2 import Environment, FileSystemLoader

class had(object):

  def __init__(self):
    template_path = os.path.join(os.path.dirname(__file__), 'templates')
    self.jinja_env = Environment(loader=FileSystemLoader(template_path),
																 autoescape=True)
    self.url_map = Map([
      Rule('/', endpoint='home'),
      Rule('/<page_title>', endpoint='section'),
      Rule('/events/<page_title>', endpoint='event')
    ])

  # ===========
  # nav
  def nav():
    base_url = "http://wikidev.hackersanddesigners.nl/"
    folder_url = "mediawiki/"
    api_call =  "api.php?"

    nav_options = {'action': 'ask', 'query': '[[Concept:+]]', 'format': 'json', 'formatversion': '2'}
    response_nav = requests.get(base_url + folder_url + api_call , params=nav_options)
    wkdata_nav = response_nav.json()
    print(response_nav.url)

    return wkdata_nav

  # ==========
  # home	
  def on_home(self, request, wkdata_nav=nav()):
    base_url = "http://wikidev.hackersanddesigners.nl/"
    folder_url = "mediawiki/"
    api_call =  "api.php?"

    # fetch intro
    intro_options = {'action': 'parse', 'pageid': '29', 'format': 'json', 'formatversion': '2'}
    intro_response = requests.get(base_url + folder_url + api_call , params=intro_options)
    wkdata_intro = intro_response.json()

    wkpage_title = wkdata_intro['parse']['title']
    wkintro = wkdata_intro['parse']['text']

    # fix rel-links to be abs-ones
    soup = BeautifulSoup(wkintro, 'html.parser')

    for a in soup.find_all('a', href=re.compile(r'^(?!(?:[a-zA-Z][a-zA-Z0-9+.-]*:|//))')):
      rel_link = a.get('href')
      out_link = urljoin(base_url, rel_link)
      a['href'] = out_link

    for img in soup.find_all('img', src=re.compile(r'^(?!(?:[a-zA-Z][a-zA-Z0-9+.-]*:|//))')):
      rel_link = img.get('src')
      out_link = urljoin(base_url, rel_link)
      img['src'] = out_link

    wkintro = soup

    # events
    category_events = "[[Category:Event]]"
    filters_events = "|?NameOfEvent|?OnDate|?Venue|?Time|sort=OnDate|order=descending"
    today = datetime.date.today()
    today = today.strftime('%Y/%m/%d')

    options_allevents = {'action': 'query', 'generator': 'categorymembers', 'gcmtitle': 'Category:Event', 'format': 'json', 'formatversion': '2'}
    response_allevents = requests.get(base_url + folder_url + api_call, params=options_allevents)
    wkdata_allevents = response_allevents.json()

    ev_pages = wkdata_allevents['query']['pages']

    ev_pageid_list = []
    for dict in ev_pages:
      ev_list = list(dict.items())
      ev_list = ev_list[0][1]
      ev_pageid_list.append(ev_list)
    print(ev_pageid_list)

    # ==========================
    # upcoming events
    date_upevents = "[[OnDate::>" + today + "]]"
    upevents_options = {'action': 'ask', 'query': category_events + date_upevents + filters_events, 'format': 'json', 'formatversion': '2'}
    response_upevents = requests.get(base_url + folder_url + api_call , params=upevents_options)
    wkdata_upevents = response_upevents.json()
    for item in wkdata_upevents['query']['results'].items():
      print('---')
      print(item)
      print('---')
    #wkdata_upevents.append(ev_pageid_list[0])
    #print(wkdata_upevents_l)

		# past events
    date_pastevents = "[[OnDate::<" + today + "]]"
    options_pastevents = {'action': 'ask', 'query': category_events + date_pastevents + filters_events, 'format': 'json', 'formatversion': '2'}

    response_pastevents = requests.get(base_url + folder_url + api_call , params=options_pastevents)
    wkdata_pastevents = response_pastevents.json()

    # ==========================
    # build template
    return self.render_template('index.html',
                                nav=wkdata_nav,
                                title=wkpage_title,
                                intro=wkintro,
                                up_event_list=wkdata_upevents,
                                past_event_list=wkdata_pastevents
                                )

  def on_section(self, request, page_title, wkdata_nav=nav()):
    base_url = "http://wikidev.hackersanddesigners.nl/"
    folder_url = "mediawiki/"
    api_call =  "api.php?"

    # fetch page-content
    page_head_options = {'action': 'parse', 'page': 'Concept:' + page_title, 'format': 'json', 'formatversion': '2'}
    response_head = requests.get(base_url + folder_url + api_call, params=page_head_options)
    wkdata_head = response_head.json()
    wk_title = wkdata_head['parse']['title']
    
    # fetch page-content
    page_content_options = {'action': 'ask', 'query': '[[Concept:' + page_title + ']]', 'format': 'json', 'formatversion': '2'}
    response_content = requests.get(base_url + folder_url + api_call, params=page_content_options)
    wkdata_content = response_content.json()

    #build template
    return self.render_template('section.html',
                                nav=wkdata_nav,
                                title=wk_title,
                                wkdata=wkdata_content
                                )


  def on_event(self, request, page_title, wkdata_nav=nav()):
    base_url = "http://wikidev.hackersanddesigners.nl/"
    folder_url = "mediawiki/"
    api_call =  "api.php?"

    # fetch page-content
    page_options = {'action': 'parse', 'page': page_title, 'format': 'json', 'formatversion': '2'}
    response_content = requests.get(base_url + folder_url + api_call, params=page_options)
    wkdata = response_content.json()
    print(response_content.url)
    print(wkdata)

    wktitle = wkdata['parse']['title']
    wkbodytext = wkdata['parse']['text']

    wkmeta = wkdata['parse']['links']
    wkdate = wkmeta[1]['title']

    # fix rel-links to be abs-ones
    soup = BeautifulSoup(wkbodytext, 'html.parser')

#		for a in soup.find_all('a', href=re.compile(r'(\/mediawiki\/.+)')):
#			rel_link = a.get('href')
#			print (rel_link)
			#out_link = urljoin(base_url, rel_link)
			#a['href'] = out_link

    for a in soup.find_all('a', href=re.compile(r'^(?!(?:[a-zA-Z][a-zA-Z0-9+.-]*:|//))')):
      rel_link = a.get('href')
      print(rel_link)
      print('===')
      #out_link = urljoin(base_url, rel_link)
      #print(out_link)
      #print('***')
      #a['href'] = out_link

    for img in soup.find_all('img', src=re.compile(r'^(?!(?:[a-zA-Z][a-zA-Z0-9+.-]*:|//))')):
      src_rel_link = img.get('src')
      srcset_rel_link = img.get('srcset')
      if (src_rel_link):
        out_link = urljoin(base_url, src_rel_link)
        img['src'] = out_link
      if (srcset_rel_link):
        srcset_list = re.split(r'[,]\s*', srcset_rel_link)
        srcset_lu = srcset_list
        srcset_list[:] = [urljoin(base_url, srcset_i) for srcset_i in srcset_list]
        srcset_s = ', '.join(srcset_lu)
        img['srcset'] = srcset_s

      # get rid of <a>s wrapping <img>s
      a_img = img.find_parent("a")
      a_img.unwrap()

    # delete wiki infobox
    infobox = soup.find('table')
    infobox.decompose()

    wkbodytext = soup

    #build template
    return self.render_template('event.html',
                                nav=wkdata_nav,
                                title=wktitle,
                                date=wkdate,
                                bodytext=wkbodytext
                                )

  def error_404(self):
    response = self.render_template('404.html')
    response.status_code = 404
    return response

  def render_template(self, template_name, **context):
    t = self.jinja_env.get_template(template_name)
    return Response(t.render(context), mimetype='text/html')

  def dispatch_request(self, request):
    adapter = self.url_map.bind_to_environ(request.environ)
    try:
      endpoint, values = adapter.match()
      return getattr(self, 'on_' + endpoint)(request, **values)
    except NotFound as e:
      return self.error_404()
    except HTTPException as e:
      return e

  def wsgi_app(self, environ, start_response):
    request = Request(environ)
    response = self.dispatch_request(request)
    return response(environ, start_response)

  def __call__(self, environ, start_response):
    return self.wsgi_app(environ, start_response)

def create_app(with_assets=True):
  app = had()
  if with_assets:
    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
      '/assets': os.path.join(os.path.dirname(__file__), 'assets')
    })
  return app

if __name__ == '__main__':
	from werkzeug.serving import run_simple
	app = create_app()
	run_simple('127.0.0.1', 5000, app, use_debugger=True, use_reloader=True)
