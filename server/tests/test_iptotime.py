import unittest
import responses
import os
import mock
from mock import *
import server.iptotime
from server.iptotime import *

class TestIpToTime(unittest.TestCase):

    def test_creatingiptotime(self):
        iptotimemap = IpToTimeMap()

        iptotimemap.store_time('192.0.1.1', 100)
        iptotimemap.store_time('192.0.1.2', 200)
        iptotimemap.store_time('192.0.1.3', 300)

        self.assertEqual(iptotimemap.is_in('192.0.1.1'), True)
        self.assertEqual(iptotimemap.is_in('192.0.1.2'), True)
        self.assertEqual(iptotimemap.is_in('192.0.1.3'), True)
        self.assertEqual(iptotimemap.is_in('192.0.2.1'), False)
        self.assertEqual(iptotimemap.is_in('192.0.2.2'), False)
        self.assertEqual(iptotimemap.is_in('192.0.2.3'), False)

        self.assertEqual(iptotimemap.get_time('192.0.1.1'), 100)
        self.assertEqual(iptotimemap.get_time('192.0.1.2'), 200)
        self.assertEqual(iptotimemap.get_time('192.0.1.3'), 300)
