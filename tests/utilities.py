import unittest
from mock import patch
from freezegun import freeze_time


class BaseTest(unittest.TestCase):
    import_route = ''

    def add_patcher(self, patch_string, import_route=None):
        import_route = import_route if import_route is not None else self.import_route
        patched = patch(f'{import_route}.{patch_string}')
        self.addCleanup(patched.stop)
        return patched.start()

    def add_freeze(self, time_to_freeze):
        freezer = freeze_time(time_to_freeze)
        self.addCleanup(freezer.stop)
        return freezer.start()
