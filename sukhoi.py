from ehp import Html
from websnake import ResponseHandle, get, post
from untwisted.iostd import LOST
from untwisted.core import die
from untwisted.task import Task, DONE
from urlparse import urlparse, urljoin
from untwisted import core
import cgi

HEADERS = {
'user-agent':'Sukhoi Web Crawler', 
'connection': 'close'}

class Fetcher(object):
    def __init__(self, miner):
        self.miner = miner
        con = get(self.miner.url, headers=self.miner.headers, 
        auth=self.miner.auth)

        self.install_handles(con)

    def install_handles(self, con):
        con.install_maps(('200', self.on_success), 
        ('302', self.on_redirect), 
        ('301', self.on_redirect))
        self.miner.task.add(con, LOST)

    def on_success(self, con, response):

        self.miner.build_dom(response)

    def on_redirect(self, con, response):
        con = get(response.headers['location'], 
        headers=self.miner.headers, auth=self.miner.auth)
        self.install_handles(con)

class Poster(Fetcher):
    def __init__(self, miner):
        self.miner = miner
        con = post(self.miner.url, 
        headers=self.miner.headers, payload=self.miner.payload)

        self.install_handles(con)

    def on_redirect(self, con, response):
        con = post(response.headers['location'], 
        headers=self.miner.headers, payload=self.miner.payload, 
        auth=self.miner.auth)

        self.install_handles(con)

class Miner(object):
    html    = Html()
    task    = Task()
    task.add_map(DONE, lambda task: die())
    task.start()

    def __init__(self, url, pool=None, max_depth=10, 
        headers=HEADERS, method='get', payload={}, auth=()):

        self.pool      = pool if pool != None else []
        self.url       = url
        self.urlparser = urlparse(url)
        self.max_depth = max_depth
        self.headers   = headers
        self.method    = method
        self.payload   = payload
        self.auth      = auth
        self.encoding  = 'utf-8'

        try:
            self.create_connection()
        except Exception as excpt:
            print excpt

    def build_dom(self, response):
        data = response.fd.read()
        type = response.headers.get('content-type', 
        'text/html; charset=%s' % self.encoding)

        params = cgi.parse_header(type)

        # Sets the encoding for later usage
        # in self.geturl for example.
        self.encoding = params[1]['charset']

        data = data.decode(self.encoding, 'ignore')
        dom  = self.html.feed(data)
        self.run(dom)

    def create_connection(self):
        if self.method == 'get':
            return Fetcher(self) 
        return Poster(self)

    def geturl(self, reference):
        """
        """
        
        # It is necessary to encode back the url
        # because websnake get method inserts the host header
        # with the wrong encoding and some web servers wouldnt
        # accept it as valid header.
        reference = reference.encode(self.encoding)
        urlparser = urlparse(reference)
        url       = urljoin('%s://%s' % (self.urlparser.scheme, 
        self.urlparser.hostname), reference) \
        if not urlparser.scheme else reference
        return url

    def next(self, reference):
        url = self.geturl(reference)
        self.__class__(url, self.pool, self.max_depth)

    def __repr__(self):
        return str(self.pool)

    def run(self, dom):
        """
        """

        pass



