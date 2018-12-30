import unittest
import server.support

import os
data_path = os.path.abspath("server/supported_websites")
class SupportWebsites(unittest.TestCase):

    def test_extractWebPageName(self):
        webpage = server.support.extractPage("www.test.com?val=123")
        self.assertEqual(webpage, "test" )

    def test_extractWebPageName2(self):
        webpage = server.support.extractPage("https://www.imperial.cloud.panopto.eu/Panopto/Pages/Viewer.aspx?id=7e65a23c-4e18-4f96-864c-a96101074cbc")
        self.assertEqual(webpage, "imperial" )

    def test_allowSupportedWebsites(self):
        allowed = server.support.isStreamLinkSupported("https://www.youtube.com/watch?v=mGIpOtncmSM", data_path)
        self.assertEqual(allowed, True)

    def test_notAllowUnsupportedWebsites(self):
        allowed = server.support.isStreamLinkSupported("https://www.imperial.cloud.panopto.eu/Panopto/Pages/Viewer.aspx?id=7e65a23c-4e18-4f96-864c-a96101074cbc", data_path)
        self.assertEqual(allowed, False)

if __name__ == '__main__':
    unittest.main()
