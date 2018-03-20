import pytest
import requests # HTTP library

from . import TestCase


class TestCfopendata(TestCase):    
    def setUp(self):
        self.year = 2017
        self.division = 1
        self.scaled = 0
        self.batchpages = 10
        self.npages = 10

        self.basepath = 'https://games.crossfit.com/competitions/api/v1/comp'+\
                        'etitions/open/'+str(self.year)+'/leaderboards?'
                        
        self.headers = {'Host': 'games.crossfit.com',
               'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2'+\
               ') AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.13'+\
               '2 Safari/537.36'}


    def test_get_page(self):
        expected = 4291
        response = requests.get(self.basepath,
                                params={"division": self.division,
                                        "scaled": self.scaled,
                                        "sort": "0",
                                        "fittest": "1",
                                        "fittest1": "0",
                                        "occupation": "0",
                                        "competition": "1",
                                        "page": 1},
                                        headers=self.headers).json()
        actual = int(response['totalpages'])
        assert expected == actual