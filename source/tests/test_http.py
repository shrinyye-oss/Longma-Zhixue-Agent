import json
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from agent_backend import AppHandler

class ApiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http=ThreadingHTTPServer(('127.0.0.1',0),AppHandler)
        cls.port=cls.http.server_address[1]
        cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True)
        cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown();cls.http.server_close()
    def url(self,path):
        return 'http://127.0.0.1:'+str(self.port)+path
    def test_home_page_served(self):
        with urlopen(self.url('/')) as r:
            text=r.read().decode('utf-8')
            self.assertIn('龙马智学',text)
            self.assertIn('knowledge-json',text)
    def test_status(self):
        with urlopen(self.url('/api/status')) as r:
            x=json.loads(r.read())
            self.assertIn('agent_enabled',x)
    def test_unconfigured_api_refuses(self):
        import agent_backend
        if agent_backend.KEY and agent_backend.MODEL:
            self.skipTest('Environment already includes live model settings')
        request=Request(self.url('/api/agent'),data=b'{"goal":"hello"}',headers={'Content-Type':'application/json'},method='POST')
        with self.assertRaises(HTTPError) as ctx:
            urlopen(request)
        self.assertEqual(ctx.exception.code,503)

if __name__=='__main__':unittest.main()
