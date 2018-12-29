import unittest
import server.support

class SupportWebsites(unittest.TestCase):

    @responses.activate
    def test_support(self):
        webpage = extractPage("www.test.com?val=123")
        self.assertEqual( webpage, "test" )
        # self.assertEqual( len( responses.calls ), 1 )

    # @responses.activate
    # def test_speechToText_exception(self):
    #     speech = server.speechtotext._convert_to_wav([-0.9, 0.45, 0, 0.42, -0.32, 0], 2000)
    #     sourceLang = "fr"
    #     mock_response = {
    #         "results": [{
    #             "Some incorrect key": "Some incorrect response"
    #         }]
    #     }
    #     responses.add(responses.POST, url,
    #               json=mock_response, status=200)
    #     text = server.speechtotext._speech_to_text(speech, 2000, sourceLang, None)
    #     self.assertEqual( text, "" )
    #     self.assertEqual( len( responses.calls ), 1 )

if __name__ == '__main__':
    unittest.main()
