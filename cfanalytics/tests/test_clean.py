from . import TestCase


class TestClean(TestCase):    
    def setUp(self):
        # Test an entry
        self.name = 'Isabelle Lange'
        self.height = '154 cm'
        self.weight = '124 lb'


    def test_weight_to_SI(self):
        expected = 56
        actual = round(int(self.weight.split(' ')[0]) / 2.2046 )
        assert expected == actual