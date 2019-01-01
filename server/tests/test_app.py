import unittest
import sys
from server.app import app, SERVER_URL, HEROKU_URL

class AppTest(unittest.TestCase):

    def setUp(self):
        app.testing = True
        self.app = app.test_client()
        pass

    def tearDown(self):
        pass

    def test_index_html(self):
        response = self.app.get("/")
        self.assertEqual(response.status_code, 200)

    def test_server_url_is_prod_url(self):
        self.assertEqual(SERVER_URL, HEROKU_URL)
