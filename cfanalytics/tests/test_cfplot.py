from . import TestCase

import math


class TestCfplot(TestCase):    
    def setUp(self):
        # Test a score
        self.regcount = 0
        self.x = self.regcount+1


    def test_rank(self):
        expected = '1$^{st}$'
        x = self.x
        ordinal = lambda x: "%d%s" %\
        (x,"tsnrhtdd"[(math.floor(x/10)%10!=1)*(x%10<4)*x%10::4])
        _o = ordinal(x)
        _o = _o.replace(str(x), "")
        actual = str(x)+'$^{'+_o+'}$'
        assert expected == actual