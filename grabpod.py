#!/usr/bin/env python

"""grabpod.py

CLI podcast fetcher.

Usage:
  grabpod.py
  grabpod.py [options] [<podcast_name> <podcast_name>...]
  grabpod.py -h | --help
  grabpod.py --version
  grabpod.py --list

Options:
  -h, --help                        Show this screen.
  --version                         Show version.
  -d, --dir=<dir>                   Download files to subdirectories of <dir>
  <podcast_name>...                 Only download these podcasts
  -n, --number-to-download=<num>    Ignore config file and download this many
                                    files from each podcast.
  -x, --dry-run                     Download podcast lists and create
                                    appropriate directories, but don't download
                                    any audio files.
  -l, --list                        List podcast names from config file.
"""

from __future__ import print_function

import json
import os
import sys
import re
from bs4 import BeautifulSoup
import urlparse
import requests
# Not using urlgrabber because it doesn't handle 302's well
from docopt import docopt

def main(args):
  if args['--version']:
    print(version)
    exit(0)
  config_dir = os.path.join(os.path.expanduser("~"), ".config")
  config_filename = os.path.join(config_dir, "grabpodrc.json")
  cur_dir = os.getcwd()

  if not os.path.exists(config_filename):
    print("{} doesn't exist so creating and populating with an example".format(config_filename))
    if not os.path.exists(config_dir):
      os.makedirs(config_dir)
    with open(config_filename, 'w') as config_file:
      example_dict = {"podcasts directory": "/tmp/boo",
"podcasts": [
{"alias": "spokenwiki",
"url": "http://feeds.feedburner.com/SpokenWiki",
"num downloads": "3"
},
{"alias": "adler",
"url": "http://www.npr.org/templates/rss/podlayer.php?id=2100166",
"num downloads": "3"
},
{"alias": "baltimore_stories",
"url": "http://www.publicbroadcasting.net/wypr/.jukebox?action=viewPodcast&podcastId=16423",
"num downloads": "4"
},
{"alias": "day6",
"url": "http://www.cbc.ca/podcasting/includes/day6.xml",
"num downloads": "2"
},
{"alias": "hdtgm",
"url": "http://rss.earwolf.com/how-did-this-get-made",
"num downloads": "2"
},
{"alias": "maher",
"url": "http://www.hbo.com/podcasts/billmaher/podcast.xml",
"num downloads": "3"
},
{"alias": "otm",
"url": "http://www.onthemedia.org/index.xml",
"num downloads": "2"
},
{"alias": "totenberg",
"url": "http://www.npr.org/templates/rss/podlayer.php?id=2101289"
},
{"alias": "waitwait",
"url": "http://www.npr.org/rss/podcast.php?id=35"
},
{"alias": "wiretap",
"url": "http://www.cbc.ca/podcasting/includes/wiretap.xml",
"num downloads": "4"
},
{"alias": "mefi",
"url": "http://feeds.feedburner.com/MeFiPodcast?format=xml",
"num downloads": "2"
},
{"alias": "revolutions",
"url": "http://revolutionspodcast.libsyn.com/rss/",
"num downloads": "3"
}
]
}
      json.dump(example_dict, config_file)

  # Read options from config file
  with open(config_filename) as config_file:
    config = json.load(config_file)
    podcasts_dir = config['podcasts directory']
    podcasts = config['podcasts']

  # If --list flag given, only list the available aliases and quit
  if args['--list']:
    for alias in (podcast['alias'] for podcast in podcasts):
      print(alias)
    exit(0)

  # CLI options override config file options
  if args['--dir'] is not None:
    podcasts_dir = args['--dir']
  if args['<podcast_name>'] != []:
    podcasts = [podcast for podcast in podcasts if podcast['alias'] in args['<podcast_name>']]

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

      # If there's some guidance on how many to download, obey it
      if args['--number-to-download'] and (int(args['--number-to-download']) > 0):
        print("  Getting top {} items".format(int(args['--number-to-download'])))
        items = parsed_xml.channel.find_all('item')[0: int(args['--number-to-download'])]
      elif "num downloads" in podcast:
        print("  Getting top {} items".format(podcast['num downloads']))
        items = parsed_xml.channel.find_all('item')[0: podcast['num downloads']]
      else:
        print("  Getting all items".format(podcast['num downloads']))
        items = parsed_xml.channel.find_all('item')
      for item in items:
        filename = urlparse.urlsplit(item.enclosure['url']).path.split('/')[-1]
        filename = os.path.join(podcast_dir, filename)
        if not os.path.exists(filename):
          asciized_item_title = item.title.get_text().encode('ascii', 'replace')
          if args['--dry-run']:
            print("Would fetch\n  {}".format(asciized_item_title))
          else:
            print("Attempting to fetch\n  {}".format(asciized_item_title))
            r =requests.get(item.enclosure['url'])
            with open(filename, 'wb') as fd:
              for chunk in r.iter_content(chunk_size=512):
                fd.write(chunk)
        else:
          print("    {}\n    already exists, skipping.".format(filename))
    except Exception, e:
      print("Exception happened")

if __name__ == "__main__":
  main(docopt(__doc__))
