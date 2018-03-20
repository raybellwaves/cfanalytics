import pytest
import requests # HTTP library

from . import TestCase


class TestAffiliatelist(TestCase):    
    def setUp(self):
        self.basepath = 'https://map.crossfit.com'
        self.headers = {'Host': 'map.crossfit.com',
               'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2'+\
               ') AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.13'+\
               '2 Safari/537.36'}


    def test_get_lat_lons(self):
        expected = 40.3604
        response = requests.get(self.basepath+'/getAllAffiliates.php').json()
        actual = response[0][0]
        assert expected == actual