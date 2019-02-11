__all__ = ['BaseResource']
import logging
from flask_restplus import Resource
from helpers.page_builder import PageBuilder


class BaseResource(Resource):

    def __init__(self, api=None):
        super().__init__(api=api)
        self.logger = logging.getLogger(__name__)
        self.page_builder = PageBuilder()
