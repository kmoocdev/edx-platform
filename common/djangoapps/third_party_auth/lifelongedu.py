from social.backends.oauth import BaseOAuth2
from django.utils.http import urlencode
import json

class LifelongeduOAuth2(BaseOAuth2):
    """Lifelongedu OAuth authentication backend"""

    print "## called LifelongeduOAuth2"

    name = 'lifelongedu'
    AUTHORIZATION_URL = 'http://myserver:8082/o/authorize'
    ACCESS_TOKEN_URL = 'http://myserver:8082/o/token/'
    SCOPE_SEPARATOR = ','
    ACCESS_TOKEN_METHOD = 'POST'
    EXTRA_DATA = [
        ('id', 'id'),
        ('expires', 'expires'),
        ('login', 'login')
    ]

    def get_user_details(self, response):
        """Return user details from Github account"""
#        return {'username': response.get('login'),
#                'email': response.get('email') or '',
#                'first_name': response.get('name'),
#                'fullname': response.get('name'),
#                'last_name': response.get('name'),
#                }

        jsonString = "{"
        jsonString += '"login":"'+response.get('login')+'"'
        jsonString += ',"email":"'+response.get('email')+'"'
        jsonString += ',"name":"'+response.get('name')+'"'
        jsonString += ',"id":"'+response.get('id')+'"'
        jsonString += '}'

        return json.loads(jsonString)


    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        url = 'http://myserver:8082/api/hello?' + urlencode({
            'access_token': access_token
        })
        try:
            return self.get_json(url)
        except ValueError:
            return None

"""
    def auth_complete(self, *args, **kwargs):
        if 'access_token' in self.data and 'code' not in self.data:
            raise AuthMissingParameter(self, 'access_token or code')
        # Token won't be available in plain server-side workflow
        token = self.data.get('access_token')
        if token:
            self.process_error(self.get_json(
                'https://www.googleapis.com/oauth2/v1/tokeninfo',
                params={'access_token': token}
            ))
        response = self.request_access_token(
            self.ACCESS_TOKEN_URL,
            data=self.auth_complete_params(),
            headers=self.auth_headers(),
            method=self.ACCESS_TOKEN_METHOD
        )
        self.process_error(response)
        return self.do_auth(response['access_token'], response=response,
                            *args, **kwargs)
"""
