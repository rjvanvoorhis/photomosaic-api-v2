import unittest
from helpers import Environment
from mock import patch
from ddt import ddt, unpack, data


@ddt
class EnvironmentTestCase(unittest.TestCase):
    @data(
        ('MOCK_VAR', 'value'),
        ('mock_var', 'value'),
        ('var_not_set', None),
    )
    @unpack
    @patch('helpers.os')
    def test(self, var_name, expected, mock_os):
        mock_os.environ = {var_name: 'value'}
        res = Environment().mock_var
        self.assertEqual(res, expected)


if __name__ == '__main__':
    unittest.main()