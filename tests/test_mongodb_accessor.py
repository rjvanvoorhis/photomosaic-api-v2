import unittest
from tests.utilities import BaseTest
from accessors import mongo_db_accessor
from mock import MagicMock, patch
from ddt import data, ddt, unpack


@ddt
class PaginatorTest(BaseTest):
    import_route = 'accessors.mongo_db_accessor'

    def setUp(self):
        self.mock_collection = MagicMock()

    def get_paginator(self, base_url=None):
        return mongo_db_accessor.Paginator(self.mock_collection, base_url)

    @data(
        (None, ''),
        ('http://localhost:5000/', 'http://localhost:5000/')
    )
    @unpack
    def test_init(self, url, exp_url):
        paginator = mongo_db_accessor.Paginator('collection', base_url=url)
        self.assertEqual(paginator.collection, 'collection')
        self.assertEqual(paginator.base_url, exp_url)

    @data(
        ({}, [{'$match': {}}, {'$sort': {'_id': 1}}]),
        ({'query': {'field': 'value'}}, [{'$match': {'field': 'value'}}, {'$sort': {'_id': 1}}]),
        ({'query': {'field': 'value'}, 'sort': {'field': -1}},
         [{'$match': {'field': 'value'}}, {'$sort': {'_id': 1, 'field': -1}}]),
        ({'query': {'field': 'value'}, 'unwind': 'field'},
         [{'$match': {'field': 'value'}}, {'$sort': {'_id': 1}}, {'$unwind': 'field'}]),
        ({'query': {'field': 'value'}, 'skip': 4}, [{'$match': {'field': 'value'}}, {'$sort': {'_id': 1}}]),
        ({'query': {'field': 'value'}, 'skip': 4, 'limit': 2},
         [{'$match': {'field': 'value'}}, {'$sort': {'_id': 1}}, {'$skip': 4}, {'$limit': 2}]),
        ({'query': {'field': 'value'}, 'projection': {'field': 1}},
         [{'$match': {'field': 'value'}}, {'$sort': {'_id': 1}}, {'$project': {'field': 1}}]),
    )
    @unpack
    def test_build_results(self, kwargs, exp_pipeline):
        paginator = self.get_paginator()
        self.mock_collection.aggregate.return_value = []
        res = paginator.build_results(**kwargs)
        self.mock_collection.aggregate.assert_called_with(exp_pipeline)
        self.assertIsInstance(res, list)

    @data(
        ({}, {}, [{'$match': {}}, {'$count': 'count'}], [], 0),
        ({}, {}, [{'$match': {}}, {'$count': 'count'}], [{'count': 4}], 4),
        ({'field': 'value'}, {},
         [{'$match': {'field': 'value'}}, {'$count': 'count'}], [{'count': 4}], 4),
        ({'field': 'value'}, 'field',
         [{'$match': {'field': 'value'}}, {'$unwind': 'field'}, {'$count': 'count'}], [{'count': 4}], 4),
    )
    @unpack
    def test_get_count(self, query, unwind, pipeline, result, count):
        self.mock_collection.aggregate.return_value = result
        paginator = self.get_paginator()
        result_count = paginator.get_count(query, unwind)
        self.mock_collection.aggregate.assert_called_with(pipeline)
        self.assertEqual(count, result_count)

    @data(
        ({}, {'query': {}, 'projection': None, 'unwind': None, 'skip': 0, 'limit': None, 'sort': None}),
        ({}, {'query': {}, 'projection': None, 'unwind': None, 'skip': 0, 'limit': None, 'sort': None}),
    )
    @unpack
    @patch.object(mongo_db_accessor.Paginator, 'get_count')
    @patch.object(mongo_db_accessor.Paginator, 'build_results')
    def test_cursor(self, kwargs, exp_kwargs, build_results, get_count):
        get_count.return_value = 1
        build_results.return_value = [{}]
        paginator = self.get_paginator()
        cursor = paginator.build_cursor(**kwargs)
        build_results.assert_called_with(**exp_kwargs)
        get_count.assert_called_with(query=exp_kwargs['query'], unwind=exp_kwargs['unwind'])
        self.assertEqual(cursor, {'total': 1, 'results': [{}]})


@ddt
class MongoDbAccessorTest(BaseTest):
    import_route = 'accessors.mongo_db_accessor'

    def setUp(self):
        self.mock_logger = self.add_patcher('logging').getLogger.return_value
        self.mock_client = self.add_patcher('MongoClient')
        self.mock_env = self.add_patcher('Environment').return_value
        self.mock_env.mongodb_uri = 'mock_uri'
        self.mock_paginator = self.add_patcher('Paginator')

    @staticmethod
    def get_accessor(cn='users'):
        return mongo_db_accessor.MongoDbAccessor(collection_name=cn)

    def test_init(self):
        accessor = self.get_accessor('users')
        self.assertEqual(accessor.collection_name, 'users')
        self.assertEqual(accessor.db, self.mock_client.return_value.photomosaic)
        self.mock_client.assert_called_with('mock_uri')
        accessor.db.__getitem__.assert_called_with('users')
        self.mock_paginator.assert_called_with(accessor.collection)

    def test_aggregate(self):
        accessor = self.get_accessor()
        accessor.aggregate(1, 2, 3, a='a', b='b')
        accessor.collection.aggregate.assert_called_with(1, 2, 3, a='a', b='b')

    @data(
        (None, None, {}, None, {'_id': 0}),
        ({}, {'field': 'value'}, {}, {}, {'field': 'value', '_id': 0}),
        ({}, {'_id': 1}, {}, {}, {'_id': 1})
    )
    @unpack
    def test_find_one(self, query, projection, kwargs, exp_query, exp_projection):
        accessor = self.get_accessor()
        accessor.collection.find_one.return_value = {'result': 'value'}
        result = accessor.find_one(query, projection, **kwargs)
        accessor.logger.debug.assert_called_with(f'Retrieving document from users with query: {query}')
        accessor.collection.find_one.assert_called_with(exp_query, exp_projection)
        self.assertEqual(result, {'result': 'value'})

    def test_update_one(self):
        accessor = self.get_accessor()
        accessor.update_one('query', 'update', a='a', b='b')
        accessor.logger.debug.assert_called_with('Updating document from users with query: query and update: update')
        accessor.collection.update_one.assert_called_with('query', 'update', a='a', b='b')

    def test_replace_one(self):
        accessor = self.get_accessor()
        accessor.replace_one('query', 'replacement', a='a', b='b')
        accessor.logger.debug.assert_called_with(
            'Replacing document from users with query: query and replacement: replacement')
        accessor.collection.replace_one.assert_called_with('query', 'replacement', a='a', b='b')

    def test_get_paginated_results(self):
        accessor = self.get_accessor()
        accessor.get_paginated_results('query', 'projection', 'unwind', 'skip', 'limit', 'sort')
        accessor.paginator.build_cursor.assert_called_with(
            'query', 'projection', 'unwind', 'skip', 'limit', 'sort')

    def test_delete_one_element(self):
        accessor = self.get_accessor()
        accessor.delete_one_element('query', 'array_field', 'element_filter')
        accessor.logger.debug.assert_called_once()
        exp_update = {'$pull': {'array_field': 'element_filter'}}
        accessor.collection.update_one.assert_called_once_with('query', exp_update)

    def test_get_array_element(self):
        exp_pipeline = [
            {'$match': 'query'},
            {'$unwind': '$array_field'},
            {'$match': 'element_filter'},
            {'$project': {'result': '$array_field', '_id': 0}}
        ]
        accessor = self.get_accessor()
        accessor.collection.aggregate.return_value = [{'result': {'doc': 'value'}}]
        res = accessor.get_array_element('query', 'array_field', 'element_filter')
        accessor.collection.aggregate.assert_called_with(exp_pipeline)
        self.assertEqual(res, {'doc': 'value'})

    @data(
        (True, None),
        (False, Exception)
    )
    @unpack
    def test_health(self, result, side_effect):
        accessor = self.get_accessor()
        accessor.client.server_info.side_effect = side_effect
        res = accessor.health()
        if not result:
            accessor.logger.exception.assert_called_once()
        self.assertEqual(res, result)


if __name__ == '__main__':
    unittest.main()