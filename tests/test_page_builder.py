import unittest
from ddt import ddt, data, unpack
from helpers.page_builder import PageBuilder
from mock import patch


URL = 'http://my_mock_url.com/collection'
SAMPLE_LINKS = [
    f'{URL}?skip=0&limit=2',
    f'{URL}?skip=2&limit=2',
    f'{URL}?skip=4&limit=2'
]
SAMPLE_NAVIGATION = {'current': SAMPLE_LINKS[0],
                     'next': SAMPLE_LINKS[1]}


@ddt
class PageBuilderTest(unittest.TestCase):
    @data(
        ('b', ['c'], {'current': 'b'}),
        ('a', ['a'], {'current': 'a'}),
        ('a', ['a', 'b'], {'current': 'a', 'next': 'b'}),
        ('b', ['a', 'b'], {'current': 'b', 'prev': 'a'}),
        ('b', ['a', 'b', 'c'], {'current': 'b', 'next': 'c', 'prev': 'a'}),
    )
    @unpack
    def test_build_navigation(self, current, links, expected):
        res = PageBuilder.build_navigation(current, links)
        self.assertEqual(res, expected)

    @data(
        (1, 5, '?skip=1&limit=5'),
        (1, 0, ''),
        (1, None, ''),
    )
    @unpack
    def test_build_url(self, skip, limit, expected):
        pb = PageBuilder()
        url = 'http://my_mock_url.com/collection'
        res = pb.build_url(url, skip, limit)
        self.assertEqual(res, f'{url}{expected}')

    @data(
        (6, 0, [URL]),
        (6, 2, SAMPLE_LINKS)
    )
    @unpack
    def test_build_links(self, total, limit, expected):
        url = 'http://my_mock_url.com/collection'
        pb = PageBuilder()
        res = pb.build_links(total, limit, url)
        self.assertEqual(res, expected)

    def test_add_navigations(self):
        results = {'total': 6, 'results': [{}, {}, {}]}
        PageBuilder().add_navigation(results, URL, 0, 2)
        self.assertEqual(results['current_page'], 0)
        self.assertEqual(results['links'], SAMPLE_LINKS)
        self.assertEqual(results['total_pages'], 3)
        self.assertEqual(results['navigation'], SAMPLE_NAVIGATION)


if __name__ == '__main__':
    unittest.main()
