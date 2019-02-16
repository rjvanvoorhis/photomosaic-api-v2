import unittest
from helpers import Environment
from tests.utilities import BaseTest
from ddt import ddt, unpack, data
# from mock import patch
# from ddt import ddt, unpack, data


@ddt
class EnvironmentTestCase(BaseTest):
    import_route = 'helpers.environment'

    def setUp(self):
        self.mock_os = self.add_patcher('os')


    @data(
        ('MOCK_VAR', 'value'),
        ('mock_var', 'value'),
        ('var_not_set', None),
    )
    @unpack
    def test(self, var_name, expected):
        self.mock_os.environ = {var_name: 'value'}
        res = Environment().mock_var
        self.assertEqual(res, expected)

    def test_singleton(self):
        self.assertTrue(Environment() is Environment())


if __name__ == '__main__':
    unittest.main()
