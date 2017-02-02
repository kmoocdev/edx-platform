#-*- coding: utf-8 -*-
""" Views for a student's account information. """

import logging
import json
import urlparse
from datetime import datetime

import logging
import json
import urlparse
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse, resolve
from django.http import (
    HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpRequest
)
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django_countries import countries
from edxmako.shortcuts import render_to_response
import pytz

from commerce.models import CommerceConfiguration
from external_auth.login_and_register import (
    login as external_auth_login,
    register as external_auth_register
)
from lang_pref.api import released_languages, all_languages
from openedx.core.djangoapps.commerce.utils import ecommerce_api_client
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.theming.helpers import is_request_in_themed_site
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_api.accounts.api import request_password_change
from openedx.core.djangoapps.user_api.errors import UserNotFound
from openedx.core.lib.time_zone_utils import TIME_ZONE_CHOICES
from openedx.core.lib.edx_api_utils import get_edx_api_data
from student.models import UserProfile
from student.views import (
    signin_user as old_login_view,
    register_user as old_register_view
)
from student.helpers import get_next_url_for_login_page
import third_party_auth
from third_party_auth import pipeline
from third_party_auth.decorators import xframe_allow_whitelisted
from util.bad_request_rate_limiter import BadRequestRateLimiter
from util.date_utils import strftime_localized

import commands
from django.views.decorators.csrf import csrf_exempt
from datetime import date
from student.views import register_user
from django.contrib.auth import authenticate
from util.json_request import JsonResponse
import time
import thread

import logging
import logging.handlers
from datetime import datetime
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
import MySQLdb as mdb
from django.core.serializers.json import DjangoJSONEncoder
from django.core.mail import send_mail
import sys
import re
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
import datetime

def comm_faq(request):
    return render_to_response('community/comm_faq.html')