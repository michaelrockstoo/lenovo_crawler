# Works with Python 3
import logging
import urllib
import urllib.request
import urllib.parse
import urllib.error
import socket
import time
import sched
import webbrowser

import re

########################################################################
# Function: content = open_url(url_str, data, header, timeout)
# Description: open the given url (with the POST message defined in data)
#
def open_url(url_str, data, header, timeout):
  if header == '':
      req = urllib.request.Request(url_str, data)
  else:
      req = urllib.request.Request(url_str, data, header)
#get the handle
  #print(url_str)
  try:
      fh = urllib.request.urlopen(url = req, timeout = 10)
      code = fh.getcode()
  except Exception as e:
      if isinstance(e, urllib.error.HTTPError):
         str_log_line = 'error # 1, http error {0}' + e.__str__()
         print (str_log_line)
         log_write(str_log_line)
         return ''
      elif isinstance(e, urllib.error.HTTPErro):
         str_log_line = 'error # 2, url error: socket timeout {0}'+ e.__str__()
         print (str_log_line)
         log_write(str_log_line)
         return ''
      else:
         str_log_line = 'error # 3:' + e.__str__()
         print (str_log_line)
         log_write(str_log_line)
         return ''
  content = ''
  try:
         content = fh.read()
  except Exception as e:
        print ('error: ' + e.__str__())
        return content.decode()
  return content.decode()

########################################################################
# Function: ret = filter_item(content)
# Description: filter the key words (machine models) on the webpage,
# do not try to include too many key words for I'm currently calling the
# web browser to finish the job of ``adding to cart'' -- it's quite slow
#
def filter_item(content):
  ret = 0;
  key_words = re.findall('X1 Carbon 3', content, re.S);
  item_num = len(key_words)

  if item_num != 0:
    ret = 0b000001

  key_words = re.findall('T450s', content, re.S);
  item_num = len(key_words)

  if item_num != 0:
    ret = 0b000010

  key_words = re.findall('Y50', content, re.S);
  item_num = len(key_words)

  if item_num != 0:
    ret = 0b000100

  key_words = re.findall('T540s', content, re.S);
  item_num = len(key_words)
  if item_num != 0:
    ret = 0b001000

  key_words = re.findall('ThinkPad W5', content, re.S);
  item_num = len(key_words)
  if item_num != 0:
    ret = 0b010000

  key_words = re.findall('P400', content, re.S);
  item_num = len(key_words)

  if item_num != 0:
    ret = 0b100000

  return ret;

########################################################################
# Function: event_func(msg)
# Description: the event to be registered to the timer. All the jobs of
# looking for items, adding to carts, etc are done here
# TODO: (1) Use a globle param for the POST message ``postdata'', and use a
# dialog to specify its content.
#   (2) Automatic payment can be done after the block of ``adding to
# cart'', however, it seems the action of button-clicking (add to cart)
# will lead to 3 GET and 1 POST with a number of resource loading messages
# (GETs), use wireshark to analyze the details of the HTTP messages.
def event_func(msg):

  header = {'User-agent': 'Safari/537.36'}
  #header = {"User-Agent":"Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36(KHTML, like Gecko) Ubuntu Chromium/31.0.1650.63 Chrome/31.0.1650.63 Safari/537.36"}

  url_str = 'http://outlet.lenovo.com/outlet_us/laptops'
  content = open_url(url_str, None, header, 10)
  if content == '':
    return
  
  category_id = re.findall(r"categoryid\: \"(.+?)\"", content, re.S)
  if len(category_id) == 0:
    #items are gone!
    print (category_id)
    return

  #POST message obtained via wireshark
  postdata = {
    'category-id':category_id[0],
    'sort-criteria':'0',
    'FacetDropDownOrientation':'vertical',
    'page-index':'1',
    'page-size':'100',
    #'facet-3':'7',  #Helix
    'facet-3':'14', #T series
    #'facet-3':'19', #X Series
    #'facet-3':'22', #Yoga
    #'facet-6':'1', #CPU i7
    #'facet-6':'2', #CPU i5
    #'facet-6':'3', #CPU i3
    #'facet-9':'4', #memory 4GB-5.99GB
    #'facet-9':'5', #memory 6GB-7.99GB
    'facet-9':'6', #memory 8GB-9.9GB
    'keyword-facet':'',
    'update-facet-id':'1'
  }
  data = urllib.parse.urlencode(postdata)
  data = data.encode("iso-8859-1")
  #print(data)
  url_str = 'http://outlet.lenovo.com/SEUILibrary/controller/e/outlet_us/LenovoPortal/en_US/catalog.workflow:GetCategoryFacetResults?q=1&catalog-type='
  content = open_url(url_str, data, header, 10)
  if content == '':
    print ("Searching condition does not match.")
    return
  #print(content)
  #get the category part of the url
  item_url = re.findall(r"url:\'//(.+?)\',", content)
  list_length = len(item_url)
  if list_length == 0:
    print ('error: no valid url.')
    raise SystemExit

  url_head = 'http://' + item_url[0] +'&page=1&itemid=';
  #log_write(url_head)
  #print url_head

  #get the item part of the url
  item_id_str = re.findall(r"var fitems = \[(.+?)\];", content, re.S);
  list_length = len(item_id_str)
  if list_length == 0:
    print ('error: no items.')
    #log_write('error: no items.')
  else:
    item_list = re.findall(r"'(.+?)',", item_id_str[0], re.S);
    indicator = 0

    if len(item_list) == 0:
      print ("no item found, check the browser response.")
      #log_write("no item found or request blocked")
    #k = 0;

    for idx in item_list:
      item_url_full = url_head + idx
      #print item_url_full
      #log_write(item_url_full)
      content = open_url(item_url_full, None, header, 10)
      if content == '':
        print ("Item list is empty.")
        return

      #dump_file('item'+str(k), content)
      #k += 1

      flag_found = filter_item(content)
      if flag_found != 0:
        #print item_url_full

        #leads to the webpage for adding to shopping cart
        content = open_url(item_url_full, None, header, 10)
        key_words = re.findall('Sold out', content, re.S);

        if content == '':
          #print "The loaded webpage is lost..."
          return
        elif len(key_words) != 0:
          #print "The item was sold out..."
          continue

        #add to shopping cart
        tmp_found = re.findall(r"<a class=\"button-called-out button-full facetedResults-cta\"(.+?)Add to cart", content, re.S)
        print(tmp_found)
        if len(tmp_found) != 0:
          new_url = re.findall(r"href=\"(.+?)\" id=", tmp_found[0], re.S)
          itemid =  re.findall(r"\?sb=(.+?)\"", tmp_found[0], re.S)
          new_addtocart_url = 'http://outlet.lenovo.com'+new_url[0]
          print(new_addtocart_url)
          #web_controller = webbrowser.get('firefox')
          #web_controller.open(new_addtocart_url)
          #content = open_url(new_addtocart_url, None, header, 10)
          #print(content)
          new_addtocart_url1 = '//outlet.lenovo.com/SEUILibrary/controller/e/outlet_us/LenovoPortal/en_US/cart.workflow:AddToCart?addtocart-item-id='+itemid[0]
          #print(new_addtocart_url1)
          webbrowser.open(new_addtocart_url)
        else:
          print ("The deal was found but lost before adding to shopping cart...")
      else:
        continue
      indicator = indicator | flag_found
    #end of for

    if indicator != 0:
      print ("Item Found!")

      if indicator & 0b000001:
        print ("X1 Carbon 2 Found in Lenovo Outlet!")
        log_write('X1 Carbon 2 Found in Lenovo Outlet')
      if indicator & 0b000010:
        print ("T450s Found in Lenovo Outlet!")
        log_write('T450s Found in Lenovo Outlet')
      if indicator & 0b000100:
        print ("Y50 Found in Lenovo Outlet!")
        log_write('Y50 Found in Lenovo Outlet')
      if indicator & 0b001000:
        print ("T540s Found in Lenovo Outlet!")
        log_write('T540s Found in Lenovo Outlet')
      if indicator & 0b010000:
        print ("W540 Found in Lenovo Outlet!")
        log_write('W5X0 Found in Lenovo Outlet')
      if indicator & 0b100000:
        print ("P400 Found in Lenovo Outlet!")
        log_write('P400 Found in Lenovo Outlet')

      print ('Items are now in store in Lenovo Outlet!', 'Warning')

########################################################################
# Function
# Description: register the event funtion to the timer
#
def run_function():
  s = sched.scheduler(time.time, time.sleep)
  s.enter(0, 2, event_func, ("Timer event.",))
  s.run()

########################################################################
# Function None = timer_run()
# Description: standard timer
# TODO: (1) it seems that the lenovo server will check the punching
#   frequency, and will return ``HTTP error 249'' according to its load.
# 1sec is a perfectly safe waiting time. Punching with a time interval
# of 0.2sec-0.5sec may work, but will soon see error 249. Sometimes
# the server will report ``session is out of time'' error, then whatever
# is added to the cart will be lost.
# NEED TO REWRITE THE CODE, a manager of ip proxy IS needed, multi-thread
# may be needed -- replace the current code by importing threading
def timer_run():
  while True:
          time.sleep(5)
    #print "Starting a new query..."
    #log_write('starting a new query')
          run_function()

########################################################################
# Function None = dump_file(file_name, content)
# Description: dump the web page content into a local file for analysis
#
def dump_file(file_name, content):
  text_file = open(file_name, "w");
  text_file.write(content)
  text_file.close()

########################################################################
# Function
# Description: dump a user message into a log file for analysis
# TODO: add some format
def log_write(str_log_line):
  logger.info(str_log_line)

########################################################################
# Entrance
#
if __name__ == "__main__":
  time_stamp = time.time();
  str_log_name = time.strftime('%Y-%m-%d-%H-%M-%S', time.gmtime(time_stamp)) +'.log'

  logger = logging.getLogger('Lenovo-Crawler')
  h_logger = logging.FileHandler(str_log_name)
  logger.addHandler(h_logger)
  logger.setLevel(logging.INFO)
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  h_logger.setFormatter(formatter)

  timer_run()
