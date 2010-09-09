import sys
import urllib

from lxml import html
from twisted.internet import defer, reactor, task
from twisted.web import client

@defer.inlineCallbacks
def login(base_url, username, password):
    cookies = dict()
    data = urllib.urlencode({"name": username, "password": password})
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        yield client.getPage(base_url + "login", method="POST",
                             followRedirect=False, headers=headers,
                             cookies=cookies, postdata=data)
    except:
        #XXX
        pass
    defer.returnValue(cookies)

@defer.inlineCallbacks
def check_links(base_url, username, password):
    cookies = yield login(base_url, username, password)

    @defer.inlineCallbacks
    def extract(url, should_parse, referrer):
        if url in already_seen:
            return
        already_seen.add(url)
        try:
            content = yield client.getPage(url, cookies=cookies)
        except Exception, e:
            print "%s is dead (%s), came from %s." % (url, str(e), referrer)
            return
        if should_parse:
            new_urls = list()
            doc = html.fromstring(content)
            doc.make_links_absolute(url)
            for (element, attr, link, _) in doc.iterlinks():
                if link in already_seen or link.startswith((base_url + "logout",
                                                            base_url + "delete",
                                                            base_url + "save")):
                    continue
                should_parse = element.tag == "a" and link.startswith(base_url)
                new_urls.append((link, should_parse, url))
            defer.returnValue(new_urls)

    def iterate(result, d):
        workers.remove(d)
        if result is not None:
            for (url, should_parse, referrer) in result:
                d = semaphore.run(extract, url, should_parse, referrer)
                d.addCallback(iterate, d)
                workers.append(d)
        if not workers:
            finished.callback(None)

    already_seen = set()
    workers = list()
    semaphore = defer.DeferredSemaphore(5)
    d = semaphore.run(extract, base_url, True, "")
    d.addCallback(iterate, d)
    workers.append(d)
    finished = defer.Deferred()
    yield finished

def main(args=None):
    if args is None:
        args = sys.argv[1:]
    check_links(*args).addBoth(lambda ignored_result: reactor.stop())
    reactor.run()
    return 0

if __name__ == "__main__":
    sys.exit(main())
