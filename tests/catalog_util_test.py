from pyudl.tds import get_latest_dods_url
from pyudl.adde.projection import int_latlon_to_float
import unittest

# http://stackoverflow.com/a/3834356
def near(a,b,rtol=1e-5,atol=1e-8):
    # rtol is relative tolerance
    # atol is absolute tolerance
    try:
        return abs(a-b)<(atol+rtol*abs(b))
    except TypeError:
        return False

class Tests(unittest.TestCase):

    def test_example(self):
        self.assertTrue(near( int_latlon_to_float(1563547),156.596388889))
        self.assertTrue(near( int_latlon_to_float(0),0))

if __name__ == '__main__':
    unittest.main()
