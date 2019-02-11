from flask import request
from resources import BaseResource
from accessors import UserAccessor
from documentation.namespaces import user_ns
from documentation.models import paging_parser, gallery_parser


@user_ns.route('/gallery')
class UserGallery(BaseResource):
    def __init__(self, api=None):
        super().__init__(api=api)
        self.accessor = UserAccessor()

    @user_ns.expect(paging_parser)
    def get(self, username):
        args = paging_parser.parse_args()
        """Get all gallery items"""
        results = self.accessor.get_paginated_list(username, 'gallery', **args)
        self.page_builder.add_navigation(results, request.base_url, **args)
        return results

    @user_ns.expect(gallery_parser)
    def post(self, username):
        payload = gallery_parser.parse_args()
        mosaic_file = payload.get('mosaic_file')
        mosaic_data = mosaic_file.read()
        mosaic_filename = mosaic_file.filename
        alternate_file = payload.get('alternate_file')
        if alternate_file:
            alternate_data = alternate_file.read()
            alternate_filename = alternate_file.filename
        else:
            alternate_filename = None
            alternate_data = None
        result = self.accessor.create_gallery_item(
            username, image_data=mosaic_data, filename=mosaic_filename,
            gif_data=alternate_data, gif_filename=alternate_filename
        )
        return result


@user_ns.route('/gallery/<string:gallery_id>')
class UserGalleryItem(BaseResource):
    def __init__(self, api=None):
        super().__init__(api=api)
        self.accessor = UserAccessor()

    def get(self, username, gallery_id):
        gallery_item = self.accessor.get_gallery_item(gallery_id, username=username)
        return gallery_item

    def delete(self, username, gallery_id):
        self.accessor.delete_gallery_item(gallery_id, username)
        return {'message': f'{gallery_id} deleted from  {username}'}