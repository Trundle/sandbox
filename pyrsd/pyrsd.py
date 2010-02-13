#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    pyrsd
    ~~~~~
    A simple Rapidshare downloader that supports RSDF and DLC files.

    :copyright: Copyright 2008-2010 by Andreas Stührk and Sebastian Ramacher.
    :license: Modified BSD.
"""

from __future__ import division, with_statement

import re
import shutil
import sys
import traceback

from binascii import unhexlify
from base64 import b64decode
from ConfigParser import ConfigParser
from contextlib import closing
from Crypto.Cipher import AES
from datetime import datetime, timedelta
from lxml import etree, html
from os.path import basename, curdir, exists, expanduser, join as pjoin
from tempfile import TemporaryFile
from time import sleep, time as ttime
from urllib2 import URLError, build_opener, install_opener, urlopen


USER_AGENT = ('Mozilla/5.0 (compatible; Konqueror/4.0; Linux) '
              'KHTML/4.0.82 (like Gecko)')

class InvalidRSURL(Exception):
    pass

class FileExists(Exception):
    pass

def download(url, outdir):
    path = pjoin(outdir, basename(url))
    if exists(path):
        raise FileExists(basename(url))
    with closing(urlopen(url)) as connection:
        spam_page = html.parse(connection)
        form = spam_page.find('.//form[@id="ff"]')
        if form is None:
            raise InvalidRSURL(url)

        dl_url = form.get('action')
    with closing(urlopen(dl_url, 'dl.start=Free')) as connection:
        data = connection.read()
        pd = re.search('(\d+) minute', data)
        if pd is not None:
            minwait = int(pd.group(1))
            starttime = (datetime.now() + timedelta(minutes=minwait))

            print "\t... waiting %d minutes (starting at %s) ..." % \
                (minwait, starttime.strftime("%x %X"))
            sleep(minwait * 60)
            return download(url, outdir)
        if re.search(r"(Currently a lot of users|There are no more download " \
            "slots|Unfortunately right now our servers are overloaded)",
            data, re.I) is not None:
            minwait = 5
            starttime = datetime.now() + timedelta(minutes=5)
            print "\t... no more download slots available - waiting %d " \
                "minutes (starting at %s) ..." % (minwait,
                        starttime.strftime("%x %X"))
            sleep(5 * 60)
            return download(url, outdir)

        timeout = int(re.search('var c=(\d+);', data).group(1))
        dl_url = re.search('<form name="dlf" action="(.*?)" ', data).group(1)

    sleep(timeout)
    # Retrieve URL
    with closing(urlopen(dl_url)) as connection:
        with TemporaryFile('w+b') as outfile:
            leeched = 0
            size = int(connection.info()['content-length'])
            starttime = ttime()
            while True:
                data = connection.read(8192)
                if not data:
                    break

                leeched += len(data)
                elapsed = ttime() - starttime
                speed = leeched / 1024 / elapsed

                sys.stdout.write('\r\t%.01f%%\tavg. down: %.01f KiB/s     ' %
                                 (leeched / size * 100, speed))
                sys.stdout.flush()
                outfile.write(data)

            # XXX: this probably needs proper handling (within urllib?)
            if leeched != size:
                print "\t... the download could have failed!" \
                    "(possible timeout, check file size)"

            outfile.seek(0)
            with open(path, 'wb') as routfile:
                shutil.copyfileobj(outfile, routfile)
    print


def decode_rsdf(filename):
    """
    Based on Dr.Hansen's RSDF Decrypter
    """

    # create crypto stuff
    key = unhexlify('8C35192D964DC3182C6F84F3252239EB4A320D2500000000')
    cipher = AES.new(key, AES.MODE_ECB)
    iv = unhexlify('F'*32)
    iv = cipher.encrypt(iv)
    aes_obj = AES.new(key, AES.MODE_CFB, iv)

    urls = []
    with open(filename) as rsd_file:
        data = rsd_file.read().strip()

        # decrypt links
        pattern = re.compile('\\x00(.*)')
        data = pattern.sub('', data)
        for link in unhexlify(''.join(data.split())).splitlines():
            l = aes_obj.decrypt(b64decode(link))
            urls.append(l.replace('CCF: ', ''))

        # without regexp
        # for link in unhexlify(data).splitlines():

    return urls

def decode_dlc(filename, key, iv, url):
    # extract data from the dlc file
    with open(filename) as dlc_file:
        data = dlc_file.read()
        dlcid = data[-88:]
        data = b64decode(data[:-88])

    # we need to get the key from the server
    with closing(urlopen(url + dlcid)) as connection:
        cdata = connection.read()
        aes = AES.new(key, AES.MODE_CBC, iv)
        k = re.search('<rc>(.+)</rc>', cdata).group(1)
        rkey = aes.decrypt(b64decode(k))

    # decrypt data
    aes = AES.new(rkey, AES.MODE_CBC, rkey)
    rdata = b64decode(aes.decrypt(data))
    xml = etree.fromstring(rdata)

    urls = []
    for u in xml.xpath('content/package/file/url'):
        urls.append(b64decode(u.text))
    return urls


def main(args=sys.argv[1:]):
    config = ConfigParser()
    config.read(expanduser('~/.pyrsdrc'))

    outdir = args[0]
    if (len(args) == 2):
        filename = args[1]
        if filename.endswith('rsdf'):
            urls = decode_rsdf(filename)
        elif filename.endswith('dlc'):
            key = config.get('DLCDecrypter', 'key')
            iv = config.get('DLCDecrypter', 'iv')
            url = config.get('DLCDecrypter', 'url')
            urls = decode_dlc(filename, key, iv, url)
    else:
        # Get list of URLs from stdin
        if sys.stdin.isatty():
            print 'Liste mit URLs eingeben:'
        urls = sys.stdin.readlines()

    # Install opener (User-Agent)
    opener = build_opener()
    opener.addheaders = [('User-agent', USER_AGENT)]
    install_opener(opener)

    for url in urls:
        url = url.strip()
        if not url or url.startswith('#'):
            continue
        print 'Downloading %s ...' % (url, )
        sys.stdout.flush()
        try:
            download(url, outdir)
        except FileExists:
            print '\t... already exists, skipping ...'
        except InvalidRSURL:
            print '\t... failed (invalid URL)'
        except URLError:
            print '\t... failed with ...'
            traceback.print_exc()
        except KeyboardInterrupt:
            raise
        except:
            print '\t... failed for some unknown reason'
            traceback.print_exc()

if __name__ == '__main__':
    try:
        if len(sys.argv) == 1:
            main([curdir])
        else:
            main()
    except KeyboardInterrupt:
        pass
