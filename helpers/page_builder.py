import math


class PageBuilder(object):

    @staticmethod
    def build_navigation(current, links):
        try:
            arr_index = links.index(current)
            sub_links = links[max(arr_index - 1, 0): arr_index + 2]
        except ValueError:
            return {'current': current}
        total = len(links)
        if total <= 1:
            keys = ['current']
        elif arr_index == 0:
            keys = ['current', 'next']
        else:
            keys = ['prev', 'current', 'next']
        return {keys[idx]: val for idx, val in enumerate(sub_links)}

    @staticmethod
    def build_query_string(skip, limit):
        return f'?skip={skip}&limit={limit}' if limit else ''

    def build_url(self, url, skip, limit):
        query_string = self.build_query_string(skip, limit)
        return f'{url}{query_string}'

    def build_links(self, total, limit, url):
        if not limit:
            return [self.build_url(url, None, limit)]
        links = [self.build_url(url, n * limit, limit) for n in range(math.ceil(total/limit))]
        return links

    def add_navigation(self, results, url, skip, limit):
        total = results.get('total', len(results.get('results', [])))
        current = self.build_url(url, skip, limit)
        links = self.build_links(total, limit, url)
        navigation = self.build_navigation(current, links)
        try:
            current_page = links.index(current)
        except ValueError:  # pragma: no cover
            current_page = 0
        results['navigation'] = navigation
        results['links'] = links
        results['total_pages'] = len(links)
        results['current_page'] = current_page
