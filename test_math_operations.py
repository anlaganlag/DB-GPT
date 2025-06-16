import unittest
from math_operations import add_numbers, divide_numbers

class TestMathOperations(unittest.TestCase):
    def test_add_numbers(self):
        # 测试两个正数相加
        self.assertEqual(add_numbers(5, 3), 8)
        # 测试一个正数和一个负数相加
        self.assertEqual(add_numbers(-2, 3), 1)
        # 测试两个负数相加
        self.assertEqual(add_numbers(-5, -3), -8)
        # 测试零的情况
        self.assertEqual(add_numbers(0, 5), 5)
        self.assertEqual(add_numbers(5, 0), 5)
        self.assertEqual(add_numbers(0, 0), 0)

    def test_divide_numbers(self):
        # 测试两个正数相除
        self.assertEqual(divide_numbers(6, 2), 3)
        # 测试一个正数和一个负数相除
        self.assertEqual(divide_numbers(-6, 2), -3)
        # 测试两个负数相除
        self.assertEqual(divide_numbers(-6, -2), 3)
        # 测试除数为零的情况
        with self.assertRaises(ValueError):
            divide_numbers(5, 0)
        # 测试被除数为零的情况
        self.assertEqual(divide_numbers(0, 5), 0)

if __name__ == "__main__":
    unittest.main()
