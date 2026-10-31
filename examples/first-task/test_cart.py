import unittest

from cart import total


class TotalTests(unittest.TestCase):
    def test_no_discount(self):
        self.assertEqual(total([(2.50, 2), (1.00, 3)]), 8.00)

    def test_ten_percent_discount(self):
        self.assertEqual(total([(20.00, 1), (5.00, 2)], discount_percent=10), 27.00)

    def test_empty_cart(self):
        self.assertEqual(total([]), 0)


if __name__ == "__main__":
    unittest.main()
