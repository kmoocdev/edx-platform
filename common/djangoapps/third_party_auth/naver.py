from social.backends.oauth import BaseOAuth2
from django.utils.http import urlencode
import json
from xml.etree import ElementTree

class NaverOAuth2(BaseOAuth2):
    """Naver OAuth authentication backend"""
    name = 'naver'
    AUTHORIZATION_URL = 'https://nid.naver.com/oauth2.0/authorize'
    ACCESS_TOKEN_URL = 'https://nid.naver.com/oauth2.0/token'
    SCOPE_SEPARATOR = ','
#   STATE_PARAMETER = 'random_state_string'
    STATE_PARAMETER = False
    REDIRECT_STATE = False
    ACCESS_TOKEN_METHOD = 'POST'
    EXTRA_DATA = [
        ('id', 'id'),
        ('expires', 'expires'),
    ]

    def get_user_details(self, response):
        """Return user details from Github account"""
#        print 'ttttttttt 000'
#        print response
#        print response.get('nickname')
        return {
#               nickname (naver id is cut as 'user***')
#               thus let's use email as username
#                'username': response.get('nickname'),
                'username': response.get('email')[0:response.get('email').index('@')],
                'email': response.get('email') or '',
                'first_name': response.get('name'),
                'provider': response.get('provider'),
                'uid': response.get('id') }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        url = 'https://apis.naver.com/nidlogin/nid/getUserProfile.xml?' + urlencode({
            'access_token': access_token
        })
#        url = 'https://121.78.115.125:8080/api/hello?' + {
#            'access_token': access_token
#        }
        try:
#            print 'ttttttttt 001'
#            print url
#            print self
            response = self.request(url)
#            print response
#            print response.content
            root = ElementTree.fromstring(response.content)
#            print 'root=', root
            #print root[0][0].text
            for child in root.iter('email'):
                xml_email=child.text
            for child1 in root.iter('name'):
                xml_name=child1.text
            for child in root.iter('id'):
                xml_id=child.text
            for child in root.iter('nickname'):
                xml_nickname=child.text

#            print xml_email, xml_id
#            print {
#                'email': xml_email,
#                'uid': xml_id,
#                'first_name': xml_name,
#                'username': xml_nickname
#            }
            json_response={
                'email': xml_email,
                'id': xml_id,
                'name': xml_name,
                'nickname': xml_nickname,
#                'username': xml_email,
                'provider': 'naver'
            }
#            print json_response
#            print json.dumps(json_response)
            #return json_response.json()
            return json_response
            #return self.get_json(url)
        except ValueError:
            return None

