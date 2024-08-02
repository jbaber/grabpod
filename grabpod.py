#!/usr/bin/env python3

__doc__ = """grabpod.py

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


import json
import os
import sys
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import requests
# Not using urlgrabber because it doesn't handle 302's well
from docopt import docopt


VERSION="0.1.0"
DEFAULT_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config")
DEFAULT_CONFIG_FILENAME = "grabpodrc.json"


class UnparseableError(Exception):
    pass


def create_default_config(config_dir, config_filename):
    if not os.path.exists(config_dir):
      os.makedirs(config_dir)
    config_path = os.path.join(config_dir, config_filename)
    with open(config_path, 'w') as config_file:
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


def fetch_podcast_xml(*, podcast, podcasts_dir):
    podcast_dir = os.path.join(podcasts_dir, podcast['alias'])
    xml_filename = os.path.join(podcast_dir, 'podcast.xml')

    if not os.path.isdir(podcast_dir):
      print(f"Creating {podcast_dir}")
      os.makedirs(podcast_dir)

    print(f"Attempting to fetch {podcast['alias']}'s podcast list to {xml_filename}")
    try:
      r = requests.get(podcast['url'])
      with open(xml_filename, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=1):
          fd.write(chunk)
    except Exception as e:
        print(e)
        exit(1)

    return xml_filename


def podcast_items_from_xml_file(*, xml_filename, num_to_download=-1):
    with open(xml_filename) as f:
        parsed_xml = BeautifulSoup(f, 'xml')
    try:
        all_items = parsed_xml.channel.find_all('item')
    except AttributeError as e:
        raise UnparseableError(f"Couldn't parse {xml_filename}")

    if all_items == None:
        raise UnparseableError(f"Couldn't parse any items from {xml_filename}")

    if num_to_download == -1:
        print("  Getting all items")
        return all_items
    else:
        print(f"  Getting top {num_to_download} items")
        try:
            return all_items[0: num_to_download]
        except Exception as e:
            print(e)
            exit(9)


def fetch_item(*, item, filepath, dry_run=True):
    if not os.path.exists(filepath):
        asciized_item_title = item.title.get_text().encode('ascii', 'replace')
        if dry_run:
            print(f"Would fetch\n  {asciized_item_title}")
            return
        else:
            print(f"Attempting to fetch\n  {asciized_item_title}")
        r = requests.get(item.enclosure['url'])
        with open(filepath, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=512):
                fd.write(chunk)
    else:
        print(f"    {filename}\n    already exists, skipping.")


def fetch_podcast(*, podcast, podcasts_dir):
    xml_filename = fetch_podcast_xml(podcast=podcast, podcasts_dir=podcasts_dir)

    print(f"Looking for links in {xml_filename}")
    num_to_download = -1
    if args['--number-to-download']:
        try:
            num_to_download = int(args['--number-to-download'])
        except ValueError as e:
            print("--number-to-download must be an integer")
            exit(2)
    elif "num downloads" in podcast:
        num_to_download = int(podcast['num downloads'])

    try:
        items = podcast_items_from_xml_file(
            xml_filename=xml_filename,
            num_to_download=num_to_download
        )
    except UnparseableError as e:
        print(f"Couldn't parse {xml_filename}")
        items = []

    for item in items:
        filepath = urlparse.urlsplit(item.enclosure['url']).path.split('/')[-1]
        filepath = os.path.join(podcast_dir, filepath)
        fetch_item(item=item, filepath=filepath, dry_run=args["--dry-run"])


def main(args):
  config_dir = DEFAULT_CONFIG_DIR
  config_path = os.path.join(config_dir, DEFAULT_CONFIG_FILENAME)
  cur_dir = os.getcwd()

  if not os.path.exists(config_path):
    print(f"{config_path} doesn't exist so creating and populating with an example")
    create_default_config(config_dir, config_path)

  # Read options from config file
  with open(config_path) as config_file:
    config = json.load(config_file)
    podcasts_dir = config['podcasts directory']
    podcasts = config['podcasts']

  # If --list flag given, only list the available aliases and quit
  if args['--list']:
    for podcast in podcasts:
        print(podcast['alias'])
    exit(0)

  # CLI options override config file options
  if args['--dir'] is not None:
    podcasts_dir = args['--dir']
  if args['<podcast_name>'] != []:
    podcasts = [podcast for podcast in podcasts if podcast['alias'] in args['<podcast_name>']]

  for podcast in podcasts:
    fetch_podcast(podcast=podcast, podcasts_dir=podcasts_dir)

if __name__ == "__main__":
  args = docopt(__doc__, version=VERSION)
  main(args)
