from kivy.network.urlrequest import UrlRequest

import base64
import json

try:
    from urllib import quote
except ImportError:
    from urllib.parse import quote


class RESTConnection:
    def __init__(self, authority, port, username, password):
        self.authority = authority
        self.port = port
        credentials = f'{username}:{password}'
        credentials = base64.standard_b64encode(credentials.encode('UTF8')).decode('UTF8')
        self.headers = {
            'Authorization': f'Basic {credentials}',
            'Content-type': 'application/json',
        }

    def construct_url(self, resource, get_parameters='', uuid=None):

        get_parameters = '&'.join(f'{quote(str(key))}={quote(str(value))}' for key, value in get_parameters.items()) \
            if get_parameters is not None else ''
        if uuid is None:
            return f'http://{self.authority}:{self.port}/openmrs/ws/rest/v1/{resource}?{get_parameters}'
        else:
            return f'http://{self.authority}:{self.port}/openmrs/ws/rest/v1/{resource}/{uuid}'

    def send_request_by_url(self, url, post_parameters, on_success, on_failure, on_error):

        UrlRequest(url, req_headers=self.headers,
                   req_body=json.dumps(post_parameters) if post_parameters is not None else None,
                   on_success=on_success, on_failure=on_failure, on_error=on_error)

    def send_request(self, resource, get_parameters, post_parameters, on_success, on_failure, on_error, uuid=None):
        url = self.construct_url(resource, get_parameters, uuid)
        print(url)
        self.send_request_by_url(url, post_parameters, on_success, on_failure, on_error)
