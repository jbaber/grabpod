from __future__ import print_function

import yaml
import pycurl
import os
import sys
import re
from bs4 import BeautifulSoup
import urlparse
import requests
# Not using urlgrabber because it doesn't handle 302's well

config_dir = os.path.join(os.path.expanduser("~"), ".config")
config_filename = os.path.join(config_dir, "grabpodrc.yaml")
cur_dir = os.getcwd()

if not os.path.exists(config_filename):
  print("{} doesn't exist so creating and populating with an example".format(config_filename))
  if not os.path.exists(config_dir):
    os.makedirs(config_dir)
  with open(config_filename, 'w') as config_file:
    config_file.write("""podcasts directory: {}

podcasts:
  - alias: day6
    url: http://www.cbc.ca/podcasting/includes/day6.xml
    num downloads: 2
  - alias: hdtgm
    url: http://rss.earwolf.com/how-did-this-get-made
    num downloads: 2""".format(cur_dir))

with open(config_filename) as config_file:
  config = yaml.load(config_file)
  podcasts_dir = config['podcasts directory']
  podcasts = config['podcasts']
      
for podcast in podcasts:
  podcast_dir = os.path.join(podcasts_dir, podcast['alias'])
  xml_filename = os.path.join(podcast_dir, 'podcast.xml')

  if not os.path.isdir(podcast_dir):
    print("Creating {}".format(podcast_dir))
    os.makedirs(podcast_dir)
  print("Attempting to fetch {0}'s podcast list to {1}".format(podcast['alias'], xml_filename))
  try:
    r =requests.get(podcast['url'])
    with open(xml_filename, 'wb') as fd:
      for chunk in r.iter_content(chunk_size=1):
        fd.write(chunk)
    # At this point download was successful
    print("Looking for links in {}".format(xml_filename))
    with open(xml_filename) as xml_file:
      parsed_xml = BeautifulSoup(xml_file, 'xml')
    if "num downloads" in podcast:
      print("  Getting top {} items".format(podcast['num downloads']))
      items = parsed_xml.channel.find_all('item')[0: podcast['num downloads']]
    else:
      items = parsed_xml.channel.find_all('item')
    for item in items:
      filename = urlparse.urlsplit(item.enclosure['url']).path.split('/')[-1]
      filename = os.path.join(podcast_dir, filename)
      if not os.path.exists(filename):
        print("Attemtping to fetch\n  {}".format(item.title.get_text()).encode('ascii', 'replace'))
        r =requests.get(item.enclosure['url'])
        with open(filename, 'wb') as fd:
          for chunk in r.iter_content(chunk_size=512):
            fd.write(chunk)
      else:
        print("    {}\n    already exists, skipping.".format(filename))
  except Exception, e:
    print("Exception happened")
