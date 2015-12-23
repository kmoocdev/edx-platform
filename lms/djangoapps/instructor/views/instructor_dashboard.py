# -*- coding: utf-8 -*-
"""
Instructor Dashboard Views
"""
import logging
import datetime
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
import uuid
import pytz

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.translation import ugettext as _, ugettext_noop
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control
from edxmako.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.utils.html import escape
from django.http import Http404, HttpResponseServerError
from django.conf import settings
from util.json_request import JsonResponse
from mock import patch

from lms.djangoapps.lms_xblock.runtime import quote_slashes
from openedx.core.lib.xblock_utils import wrap_xblock
from xmodule.html_module import HtmlDescriptor
from xmodule.modulestore.django import modulestore
from xmodule.tabs import CourseTab
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds
from courseware.access import has_access
from courseware.courses import get_course_by_id, get_studio_url
from django_comment_client.utils import has_forum_access
from django_comment_common.models import FORUM_ROLE_ADMINISTRATOR
from student.models import CourseEnrollment
from shoppingcart.models import Coupon, PaidCourseRegistration, CourseRegCodeItem
from course_modes.models import CourseMode, CourseModesArchive
from student.roles import CourseFinanceAdminRole, CourseSalesAdminRole
from certificates.models import CertificateGenerationConfiguration
from certificates import api as certs_api

from class_dashboard.dashboard_data import get_section_display_name, get_array_section_has_problem
from .tools import get_units_with_due_date, title_or_url, bulk_email_is_enabled_for_course
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from pymongo import MongoClient
import MySQLdb as mdb
import sys
from django.http import HttpResponse
from django.utils import simplejson
import csv


log = logging.getLogger(__name__)


class InstructorDashboardTab(CourseTab):
    """
    Defines the Instructor Dashboard view type that is shown as a course tab.
    """

    type = "instructor"
    title = ugettext_noop('Instructor')
    view_name = "instructor_dashboard"
    is_dynamic = True    # The "Instructor" tab is instead dynamically added when it is enabled

    @classmethod
    def is_enabled(cls, course, user=None):  # pylint: disable=unused-argument,redefined-outer-name
        """
        Returns true if the specified user has staff access.
        """
        return user and has_access(user, 'staff', course, course.id)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def instructor_dashboard_2(request, course_id):
    """ Display the instructor dashboard for a course. """
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        log.error(u"Unable to find course with course key %s while loading the Instructor Dashboard.", course_id)
        return HttpResponseServerError()

    course = get_course_by_id(course_key, depth=0)

    access = {
        'admin': request.user.is_staff,
        'instructor': has_access(request.user, 'instructor', course),
        'finance_admin': CourseFinanceAdminRole(course_key).has_user(request.user),
        'sales_admin': CourseSalesAdminRole(course_key).has_user(request.user),
        'staff': has_access(request.user, 'staff', course),
        'forum_admin': has_forum_access(request.user, course_key, FORUM_ROLE_ADMINISTRATOR),
    }

    if not access['staff']:
        raise Http404()

    is_white_label = CourseMode.is_white_label(course_key)

    sections = [
        _section_course_info(course, access),
        _section_membership(course, access, is_white_label),
        _section_cohort_management(course, access),
        _section_student_admin(course, access),
        _section_data_download(course, access),
        _section_analytics(course, access),
    ]

    #check if there is corresponding entry in the CourseMode Table related to the Instructor Dashboard course
    course_mode_has_price = False
    paid_modes = CourseMode.paid_modes_for_course(course_key)
    if len(paid_modes) == 1:
        course_mode_has_price = True
    elif len(paid_modes) > 1:
        log.error(
            u"Course %s has %s course modes with payment options. Course must only have "
            u"one paid course mode to enable eCommerce options.",
            unicode(course_key), len(paid_modes)
        )

    if (settings.FEATURES.get('INDIVIDUAL_DUE_DATES') and access['instructor']):
        sections.insert(3, _section_extensions(course))

    # Gate access to course email by feature flag & by course-specific authorization
    if bulk_email_is_enabled_for_course(course_key):
        sections.append(_section_send_email(course, access))

    # Gate access to Metrics tab by featue flag and staff authorization
    if settings.FEATURES['CLASS_DASHBOARD'] and access['staff']:
        sections.append(_section_metrics(course, access))

    # Gate access to Ecommerce tab
    if course_mode_has_price and (access['finance_admin'] or access['sales_admin']):
        sections.append(_section_e_commerce(course, access, paid_modes[0], is_white_label, is_white_label))

    # Certificates panel
    # This is used to generate example certificates
    # and enable self-generated certificates for a course.
    certs_enabled = CertificateGenerationConfiguration.current().enabled
    if certs_enabled and access['admin']:
        sections.append(_section_certificates(course))

    disable_buttons = not _is_small_course(course_key)

    analytics_dashboard_message = None
    if settings.ANALYTICS_DASHBOARD_URL:
        # Construct a URL to the external analytics dashboard
        analytics_dashboard_url = '{0}/courses/{1}'.format(settings.ANALYTICS_DASHBOARD_URL, unicode(course_key))
        link_start = "<a href=\"{}\" target=\"_blank\">".format(analytics_dashboard_url)
        analytics_dashboard_message = _("To gain insights into student enrollment and participation {link_start}visit {analytics_dashboard_name}, our new course analytics product{link_end}.")
        analytics_dashboard_message = analytics_dashboard_message.format(
            link_start=link_start, link_end="</a>", analytics_dashboard_name=settings.ANALYTICS_DASHBOARD_NAME)

    context = {
        'course': course,
        'old_dashboard_url': reverse('instructor_dashboard_legacy', kwargs={'course_id': unicode(course_key)}),
        'studio_url': get_studio_url(course, 'course'),
        'sections': sections,
        'disable_buttons': disable_buttons,
        'analytics_dashboard_message': analytics_dashboard_message,
        'is_assessment': check_assessment(course.wiki_slug),
        'is_assessment_ing' : check_assessment_ing(course_key.course),
        'is_assessment_done' : check_assessment_done(course_key.course)
    }

    return render_to_response('instructor/instructor_dashboard_2/instructor_dashboard_2.html', context)


def check_assessment(active_versions_key):
    client = MongoClient(settings.CONTENTSTORE.get('DOC_STORE_CONFIG').get('host'), settings.CONTENTSTORE.get('DOC_STORE_CONFIG').get('port'))
    db = client.edxapp

    cursor = db.modulestore.active_versions.find({'search_targets.wiki_slug':active_versions_key})
    for document in cursor:
        assessmentId = document.get('versions').get('published-branch')
    cursor.close()

    cursor = db.modulestore.structures.find({'_id':assessmentId})
    for document in cursor:
        blocks = document.get('blocks')
    cursor.close()
    client.close()
    is_assessment = False
    for block in blocks:
        if block.get('block_type') == 'openassessment':
            is_assessment = True

    return is_assessment


def check_assessment_ing(course_id):
    con = mdb.connect(settings.DATABASES.get('default').get('HOST'), settings.DATABASES.get('default').get('USER'), settings.DATABASES.get('default').get('PASSWORD'), settings.DATABASES.get('default').get('NAME'));
    cur = con.cursor()
    query = "select class_id from vw_copykiller where class_id = '"+course_id+"'"
    cur.execute(query)
    cur_rowcount = cur.rowcount
    cur.close()
    con.close()
    if cur_rowcount > 0:
        return True
    else:
        return False


def check_assessment_done(course_id):
    con = mdb.connect(settings.DATABASES.get('default').get('HOST'), settings.DATABASES.get('default').get('USER'), settings.DATABASES.get('default').get('PASSWORD'), settings.DATABASES.get('default').get('NAME'));
    cur = con.cursor()

    query = "select count(uri) from vw_copykiller where class_id ='"+course_id+"'"
    cur.execute(query)
    result = cur.fetchone()
    if result[0] == 0:
        return False

    query2 = "select "
    query2 += "    if(count(uri) = ("+query+"), 'True', 'False') complete "
    query2 += "from tb_copykiller_copyratio "
    query2 += "where "
    query2 += "    uri in (select uri from vw_copykiller where class_id ='"+course_id+"') "
    query2 += "and "
    query2 += "    complete_status = 'Y' and check_type='internet'"
    cur.execute(query2)
    result = cur.fetchone()
    cur.close()
    con.close()

    if result[0] == 'True':
        return True
    else:
        return False


## Section functions starting with _section return a dictionary of section data.

## The dictionary must include at least {
##     'section_key': 'circus_expo'
##     'section_display_name': 'Circus Expo'
## }

## section_key will be used as a css attribute, javascript tie-in, and template import filename.
## section_display_name will be used to generate link titles in the nav bar.


def _section_e_commerce(course, access, paid_mode, coupons_enabled, reports_enabled):
    """ Provide data for the corresponding dashboard section """
    course_key = course.id
    coupons = Coupon.objects.filter(course_id=course_key).order_by('-is_active')
    course_price = paid_mode.min_price

    total_amount = None
    if access['finance_admin']:
        single_purchase_total = PaidCourseRegistration.get_total_amount_of_purchased_item(course_key)
        bulk_purchase_total = CourseRegCodeItem.get_total_amount_of_purchased_item(course_key)
        total_amount = single_purchase_total + bulk_purchase_total

    section_data = {
        'section_key': 'e-commerce',
        'section_display_name': _('E-Commerce'),
        'access': access,
        'course_id': unicode(course_key),
        'currency_symbol': settings.PAID_COURSE_REGISTRATION_CURRENCY[1],
        'ajax_remove_coupon_url': reverse('remove_coupon', kwargs={'course_id': unicode(course_key)}),
        'ajax_get_coupon_info': reverse('get_coupon_info', kwargs={'course_id': unicode(course_key)}),
        'get_user_invoice_preference_url': reverse('get_user_invoice_preference', kwargs={'course_id': unicode(course_key)}),
        'sale_validation_url': reverse('sale_validation', kwargs={'course_id': unicode(course_key)}),
        'ajax_update_coupon': reverse('update_coupon', kwargs={'course_id': unicode(course_key)}),
        'ajax_add_coupon': reverse('add_coupon', kwargs={'course_id': unicode(course_key)}),
        'get_sale_records_url': reverse('get_sale_records', kwargs={'course_id': unicode(course_key)}),
        'get_sale_order_records_url': reverse('get_sale_order_records', kwargs={'course_id': unicode(course_key)}),
        'instructor_url': reverse('instructor_dashboard', kwargs={'course_id': unicode(course_key)}),
        'get_registration_code_csv_url': reverse('get_registration_codes', kwargs={'course_id': unicode(course_key)}),
        'generate_registration_code_csv_url': reverse('generate_registration_codes', kwargs={'course_id': unicode(course_key)}),
        'active_registration_code_csv_url': reverse('active_registration_codes', kwargs={'course_id': unicode(course_key)}),
        'spent_registration_code_csv_url': reverse('spent_registration_codes', kwargs={'course_id': unicode(course_key)}),
        'set_course_mode_url': reverse('set_course_mode_price', kwargs={'course_id': unicode(course_key)}),
        'download_coupon_codes_url': reverse('get_coupon_codes', kwargs={'course_id': unicode(course_key)}),
        'enrollment_report_url': reverse('get_enrollment_report', kwargs={'course_id': unicode(course_key)}),
        'exec_summary_report_url': reverse('get_exec_summary_report', kwargs={'course_id': unicode(course_key)}),
        'list_financial_report_downloads_url': reverse('list_financial_report_downloads',
                                                       kwargs={'course_id': unicode(course_key)}),
        'list_instructor_tasks_url': reverse('list_instructor_tasks', kwargs={'course_id': unicode(course_key)}),
        'look_up_registration_code': reverse('look_up_registration_code', kwargs={'course_id': unicode(course_key)}),
        'coupons': coupons,
        'sales_admin': access['sales_admin'],
        'coupons_enabled': coupons_enabled,
        'reports_enabled': reports_enabled,
        'course_price': course_price,
        'total_amount': total_amount
    }
    return section_data


def _section_certificates(course):
    """Section information for the certificates panel.

    The certificates panel allows global staff to generate
    example certificates and enable self-generated certificates
    for a course.

    Arguments:
        course (Course)

    Returns:
        dict

    """
    example_cert_status = certs_api.example_certificates_status(course.id)

    # Allow the user to enable self-generated certificates for students
    # *only* once a set of example certificates has been successfully generated.
    # If certificates have been misconfigured for the course (for example, if
    # the PDF template hasn't been uploaded yet), then we don't want
    # to turn on self-generated certificates for students!
    can_enable_for_course = (
        example_cert_status is not None and
        all(
            cert_status['status'] == 'success'
            for cert_status in example_cert_status
        )
    )
    instructor_generation_enabled = settings.FEATURES.get('CERTIFICATES_INSTRUCTOR_GENERATION', False)

    return {
        'section_key': 'certificates',
        'section_display_name': _('Certificates'),
        'example_certificate_status': example_cert_status,
        'can_enable_for_course': can_enable_for_course,
        'enabled_for_course': certs_api.cert_generation_enabled(course.id),
        'instructor_generation_enabled': instructor_generation_enabled,
        'urls': {
            'generate_example_certificates': reverse(
                'generate_example_certificates',
                kwargs={'course_id': course.id}
            ),
            'enable_certificate_generation': reverse(
                'enable_certificate_generation',
                kwargs={'course_id': course.id}
            ),
            'start_certificate_generation': reverse(
                'start_certificate_generation',
                kwargs={'course_id': course.id}
            ),
            'list_instructor_tasks_url': reverse(
                'list_instructor_tasks',
                kwargs={'course_id': course.id}
            ),
        }
    }


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_POST
@login_required
def set_course_mode_price(request, course_id):
    """
    set the new course price and add new entry in the CourseModesArchive Table
    """
    try:
        course_price = int(request.POST['course_price'])
    except ValueError:
        return JsonResponse(
            {'message': _("Please Enter the numeric value for the course price")},
            status=400)  # status code 400: Bad Request

    currency = request.POST['currency']
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    course_honor_mode = CourseMode.objects.filter(mode_slug='honor', course_id=course_key)
    if not course_honor_mode:
        return JsonResponse(
            {'message': _("CourseMode with the mode slug({mode_slug}) DoesNotExist").format(mode_slug='honor')},
            status=400)  # status code 400: Bad Request

    CourseModesArchive.objects.create(
        course_id=course_id, mode_slug='honor', mode_display_name='Honor Code Certificate',
        min_price=getattr(course_honor_mode[0], 'min_price'), currency=getattr(course_honor_mode[0], 'currency'),
        expiration_datetime=datetime.datetime.now(pytz.utc), expiration_date=datetime.date.today()
    )
    course_honor_mode.update(
        min_price=course_price,
        currency=currency
    )
    return JsonResponse({'message': _("CourseMode price updated successfully")})


def _section_course_info(course, access):
    """ Provide data for the corresponding dashboard section """
    course_key = course.id

    section_data = {
        'section_key': 'course_info',
        'section_display_name': _('Course Info'),
        'access': access,
        'course_id': course_key,
        'course_display_name': course.display_name,
        'has_started': course.has_started(),
        'has_ended': course.has_ended(),
        'list_instructor_tasks_url': reverse('list_instructor_tasks', kwargs={'course_id': unicode(course_key)}),
    }

    if settings.FEATURES.get('DISPLAY_ANALYTICS_ENROLLMENTS'):
        section_data['enrollment_count'] = CourseEnrollment.objects.enrollment_counts(course_key)

    if settings.ANALYTICS_DASHBOARD_URL:
        dashboard_link = _get_dashboard_link(course_key)
        message = _("Enrollment data is now available in {dashboard_link}.").format(dashboard_link=dashboard_link)
        section_data['enrollment_message'] = message

    if settings.FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'):
        section_data['detailed_gitlogs_url'] = reverse('gitlogs_detail', kwargs={'course_id': unicode(course_key)})

    try:
        advance = lambda memo, (letter, score): "{}: {}, ".format(letter, score) + memo
        section_data['grade_cutoffs'] = reduce(advance, course.grade_cutoffs.items(), "")[:-2]
    except Exception:  # pylint: disable=broad-except
        section_data['grade_cutoffs'] = "Not Available"
    # section_data['offline_grades'] = offline_grades_available(course_key)

    try:
        section_data['course_errors'] = [(escape(a), '') for (a, _unused) in modulestore().get_course_errors(course.id)]
    except Exception:  # pylint: disable=broad-except
        section_data['course_errors'] = [('Error fetching errors', '')]

    return section_data


def _section_membership(course, access, is_white_label):
    """ Provide data for the corresponding dashboard section """
    course_key = course.id
    ccx_enabled = settings.FEATURES.get('CUSTOM_COURSES_EDX', False) and course.enable_ccx
    section_data = {
        'section_key': 'membership',
        'section_display_name': _('Membership'),
        'access': access,
        'ccx_is_enabled': ccx_enabled,
        'is_white_label': is_white_label,
        'enroll_button_url': reverse('students_update_enrollment', kwargs={'course_id': unicode(course_key)}),
        'unenroll_button_url': reverse('students_update_enrollment', kwargs={'course_id': unicode(course_key)}),
        'upload_student_csv_button_url': reverse('register_and_enroll_students', kwargs={'course_id': unicode(course_key)}),
        'modify_beta_testers_button_url': reverse('bulk_beta_modify_access', kwargs={'course_id': unicode(course_key)}),
        'list_course_role_members_url': reverse('list_course_role_members', kwargs={'course_id': unicode(course_key)}),
        'modify_access_url': reverse('modify_access', kwargs={'course_id': unicode(course_key)}),
        'list_forum_members_url': reverse('list_forum_members', kwargs={'course_id': unicode(course_key)}),
        'update_forum_role_membership_url': reverse('update_forum_role_membership', kwargs={'course_id': unicode(course_key)}),
    }
    return section_data


def _section_cohort_management(course, access):
    """ Provide data for the corresponding cohort management section """
    course_key = course.id
    section_data = {
        'section_key': 'cohort_management',
        'section_display_name': _('Cohorts'),
        'access': access,
        'course_cohort_settings_url': reverse(
            'course_cohort_settings',
            kwargs={'course_key_string': unicode(course_key)}
        ),
        'cohorts_url': reverse('cohorts', kwargs={'course_key_string': unicode(course_key)}),
        'upload_cohorts_csv_url': reverse('add_users_to_cohorts', kwargs={'course_id': unicode(course_key)}),
        'discussion_topics_url': reverse('cohort_discussion_topics', kwargs={'course_key_string': unicode(course_key)}),
    }
    return section_data


def _is_small_course(course_key):
    """ Compares against MAX_ENROLLMENT_INSTR_BUTTONS to determine if course enrollment is considered small. """
    is_small_course = False
    enrollment_count = CourseEnrollment.objects.num_enrolled_in(course_key)
    max_enrollment_for_buttons = settings.FEATURES.get("MAX_ENROLLMENT_INSTR_BUTTONS")
    if max_enrollment_for_buttons is not None:
        is_small_course = enrollment_count <= max_enrollment_for_buttons
    return is_small_course


def _section_student_admin(course, access):
    """ Provide data for the corresponding dashboard section """
    course_key = course.id
    is_small_course = _is_small_course(course_key)

    section_data = {
        'section_key': 'student_admin',
        'section_display_name': _('Student Admin'),
        'access': access,
        'is_small_course': is_small_course,
        'get_student_progress_url_url': reverse('get_student_progress_url', kwargs={'course_id': unicode(course_key)}),
        'enrollment_url': reverse('students_update_enrollment', kwargs={'course_id': unicode(course_key)}),
        'reset_student_attempts_url': reverse('reset_student_attempts', kwargs={'course_id': unicode(course_key)}),
        'reset_student_attempts_for_entrance_exam_url': reverse(
            'reset_student_attempts_for_entrance_exam',
            kwargs={'course_id': unicode(course_key)},
        ),
        'rescore_problem_url': reverse('rescore_problem', kwargs={'course_id': unicode(course_key)}),
        'rescore_entrance_exam_url': reverse('rescore_entrance_exam', kwargs={'course_id': unicode(course_key)}),
        'student_can_skip_entrance_exam_url': reverse(
            'mark_student_can_skip_entrance_exam',
            kwargs={'course_id': unicode(course_key)},
        ),
        'list_instructor_tasks_url': reverse('list_instructor_tasks', kwargs={'course_id': unicode(course_key)}),
        'list_entrace_exam_instructor_tasks_url': reverse('list_entrance_exam_instructor_tasks',
                                                          kwargs={'course_id': unicode(course_key)}),
        'spoc_gradebook_url': reverse('spoc_gradebook', kwargs={'course_id': unicode(course_key)}),
    }
    return section_data


def _section_extensions(course):
    """ Provide data for the corresponding dashboard section """
    section_data = {
        'section_key': 'extensions',
        'section_display_name': _('Extensions'),
        'units_with_due_dates': [(title_or_url(unit), unicode(unit.location))
                                 for unit in get_units_with_due_date(course)],
        'change_due_date_url': reverse('change_due_date', kwargs={'course_id': unicode(course.id)}),
        'reset_due_date_url': reverse('reset_due_date', kwargs={'course_id': unicode(course.id)}),
        'show_unit_extensions_url': reverse('show_unit_extensions', kwargs={'course_id': unicode(course.id)}),
        'show_student_extensions_url': reverse('show_student_extensions', kwargs={'course_id': unicode(course.id)}),
    }
    return section_data


def _section_data_download(course, access):
    """ Provide data for the corresponding dashboard section """
    course_key = course.id
    section_data = {
        'section_key': 'data_download',
        'section_display_name': _('Data Download'),
        'access': access,
        'get_grading_config_url': reverse('get_grading_config', kwargs={'course_id': unicode(course_key)}),
        'get_students_features_url': reverse('get_students_features', kwargs={'course_id': unicode(course_key)}),
        'get_students_who_may_enroll_url': reverse(
            'get_students_who_may_enroll', kwargs={'course_id': unicode(course_key)}
        ),
        'get_anon_ids_url': reverse('get_anon_ids', kwargs={'course_id': unicode(course_key)}),
        'list_instructor_tasks_url': reverse('list_instructor_tasks', kwargs={'course_id': unicode(course_key)}),
        'list_report_downloads_url': reverse('list_report_downloads', kwargs={'course_id': unicode(course_key)}),
        'calculate_grades_csv_url': reverse('calculate_grades_csv', kwargs={'course_id': unicode(course_key)}),
        'problem_grade_report_url': reverse('problem_grade_report', kwargs={'course_id': unicode(course_key)}),
    }
    return section_data


def null_applicable_aside_types(block):  # pylint: disable=unused-argument
    """
    get_aside method for monkey-patching into applicable_aside_types
    while rendering an HtmlDescriptor for email text editing. This returns
    an empty list.
    """
    return []


def _section_send_email(course, access):
    """ Provide data for the corresponding bulk email section """
    course_key = course.id

    # Monkey-patch applicable_aside_types to return no asides for the duration of this render
    with patch.object(course.runtime, 'applicable_aside_types', null_applicable_aside_types):
        # This HtmlDescriptor is only being used to generate a nice text editor.
        html_module = HtmlDescriptor(
            course.system,
            DictFieldData({'data': ''}),
            ScopeIds(None, None, None, course_key.make_usage_key('html', 'fake'))
        )
        fragment = course.system.render(html_module, 'studio_view')
    fragment = wrap_xblock(
        'LmsRuntime', html_module, 'studio_view', fragment, None,
        extra_data={"course-id": unicode(course_key)},
        usage_id_serializer=lambda usage_id: quote_slashes(unicode(usage_id)),
        # Generate a new request_token here at random, because this module isn't connected to any other
        # xblock rendering.
        request_token=uuid.uuid1().get_hex()
    )
    email_editor = fragment.content
    section_data = {
        'section_key': 'send_email',
        'section_display_name': _('Email'),
        'access': access,
        'send_email': reverse('send_email', kwargs={'course_id': unicode(course_key)}),
        'editor': email_editor,
        'list_instructor_tasks_url': reverse(
            'list_instructor_tasks', kwargs={'course_id': unicode(course_key)}
        ),
        'email_background_tasks_url': reverse(
            'list_background_email_tasks', kwargs={'course_id': unicode(course_key)}
        ),
        'email_content_history_url': reverse(
            'list_email_content', kwargs={'course_id': unicode(course_key)}
        ),
    }
    return section_data


def _get_dashboard_link(course_key):
    """ Construct a URL to the external analytics dashboard """
    analytics_dashboard_url = '{0}/courses/{1}'.format(settings.ANALYTICS_DASHBOARD_URL, unicode(course_key))
    link = u"<a href=\"{0}\" target=\"_blank\">{1}</a>".format(analytics_dashboard_url,
                                                               settings.ANALYTICS_DASHBOARD_NAME)
    return link


def _section_analytics(course, access):
    """ Provide data for the corresponding dashboard section """
    course_key = course.id
    section_data = {
        'section_key': 'instructor_analytics',
        'section_display_name': _('Analytics'),
        'access': access,
        'get_distribution_url': reverse('get_distribution', kwargs={'course_id': unicode(course_key)}),
        'proxy_legacy_analytics_url': reverse('proxy_legacy_analytics', kwargs={'course_id': unicode(course_key)}),
    }

    if settings.ANALYTICS_DASHBOARD_URL:
        dashboard_link = _get_dashboard_link(course_key)
        message = _("Demographic data is now available in {dashboard_link}.").format(dashboard_link=dashboard_link)
        section_data['demographic_message'] = message

    return section_data


def _section_metrics(course, access):
    """Provide data for the corresponding dashboard section """
    course_key = course.id
    section_data = {
        'section_key': 'metrics',
        'section_display_name': _('Metrics'),
        'access': access,
        'course_id': unicode(course_key),
        'sub_section_display_name': get_section_display_name(course_key),
        'section_has_problem': get_array_section_has_problem(course_key),
        'get_students_opened_subsection_url': reverse('get_students_opened_subsection'),
        'get_students_problem_grades_url': reverse('get_students_problem_grades'),
        'post_metrics_data_csv_url': reverse('post_metrics_data_csv'),
    }
    return section_data


def return_course(course_id):
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        log.error(u"Unable to find course with course key %s while loading the Instructor Dashboard.", course_id)
        return HttpResponseServerError()

    course = get_course_by_id(course_key, depth=0)

    return course


def get_assessment_info(course):
    client = MongoClient(settings.CONTENTSTORE.get('DOC_STORE_CONFIG').get('host'), settings.CONTENTSTORE.get('DOC_STORE_CONFIG').get('port'))
    db = client.edxapp
    cursor = db.modulestore.active_versions.find({'search_targets.wiki_slug':course.wiki_slug})
    for document in cursor:
        published_branch = document.get('versions').get('published-branch')
    cursor.close()
    cursor = db.modulestore.structures.find({'_id':published_branch})
    for document in cursor:
        blocks = document.get('blocks')
        for block in blocks:
            fields = block.get('fields')
            if (block.get('block_type') == 'openassessment') and fields.has_key('submission_start') and fields.has_key('submission_due'):
                arr_submission_start = fields['submission_start'].split('+')
                arr_submission_due = fields['submission_due'].split('+')
                accessment_info = {'display_name': fields['display_name'], 'submission_start': arr_submission_start[0].replace('-', '').replace(':', '').replace('T', ''), 'submission_due': arr_submission_due[0].replace('-', '').replace(':', '').replace('T', '')}
    cursor.close()
    client.close()

    return accessment_info


def create_temp_answer(course_id):
    reload(sys)
    sys.setdefaultencoding('utf-8')
    con = mdb.connect(settings.DATABASES.get('default').get('HOST'), settings.DATABASES.get('default').get('USER'), settings.DATABASES.get('default').get('PASSWORD'), settings.DATABASES.get('default').get('NAME'));
    query = "delete from tb_tmp_answer where course_id = '"+course_id+"'"
    cur = con.cursor()
    cur.execute(query)

    query1 = "select uuid, raw_answer from submissions_submission "
    arr_course_id = course_id.split('+')
    query3 = "delete from vw_copykiller where class_id='"+arr_course_id[1]+"'"
    with con:
        cur.execute("set names utf8")
        cur.execute(query1)
        for (uuid, raw_answer) in cur:
            answer = raw_answer.replace('{"parts": [{"text": "', '').replace('"}]}','')
            answer = answer.decode('unicode_escape')
            answer = answer.replace("\'", "\\\'")
            answer = answer.encode('utf-8')
            answer = answer.decode('utf-8')
            query2 = "insert into tb_tmp_answer (course_id, uuid, raw_answer) "
            query2 += "select '"+course_id+"', '"+uuid+"', '"+answer+"' "
            query2 = str(query2)
            cur.execute(query2)
        cur.execute(query3)
    cur.close()
    con.close()


def copykiller(request, course_id):
    reload(sys)
    sys.setdefaultencoding('utf-8')
    course = return_course(course_id)
    assessment_info = get_assessment_info(course)
    create_temp_answer(course_id)
    con = mdb.connect(settings.DATABASES.get('default').get('HOST'), settings.DATABASES.get('default').get('USER'), settings.DATABASES.get('default').get('PASSWORD'), settings.DATABASES.get('default').get('NAME'));
    query = "insert into vw_copykiller"
    query += "( uri, year_id, year_name, term_id, term_name, class_id, class_name, report_id, report_name,"
    query += "student_id, student_name, student_number, start_date, end_date, submit_date, title, content ) "
    query += "select "
    query += "submission_uuid, "
    query += "year(curdate()) year_id, concat(year(curdate()), '년') year_name, "
    query += "'" + str(course.id.run) + "' term_id, '" + str(course.id.run) + "' term_name, "
    query += "'" + str(course.id.course) + "' class_id, '"+ str(course.display_name) +"' class_name, "
    query += "item_id report_id, '"+str(assessment_info['display_name'])+"' report_name, "
    query += "(select user.username from auth_user user where user.id=(select anony.user_id from student_anonymoususerid anony where anony.anonymous_user_id=student_id)) student_id, "
    query += "(select profile.name from auth_userprofile profile where profile.id=(select anony.user_id from student_anonymoususerid anony where anony.anonymous_user_id=student_id)) student_name, "
    query += "(select user.id from auth_user user where user.id=(select anony.user_id from student_anonymoususerid anony where anony.anonymous_user_id=student_id)) student_number, "
    query += "'"+str(assessment_info['submission_start'])+"' start_date, "
    query += "'"+str(assessment_info['submission_due'])+"' end_date, "
    query += "completed_at submit_date, "
    query += "'"+str(assessment_info['display_name'])+"' title, "
    query += "(select answer.raw_answer from tb_tmp_answer answer where answer.uuid=submission_uuid) content "
    query += "from "
    query += "assessment_peerworkflow "
    query += "where "
    query += "completed_at is not null and item_id not like '%DEMOk%' and course_id = '"+str(course_id)+"'"
    query1 = "delete from tb_tmp_answer"

    with con:
        cur = con.cursor()
        cur.execute("set names utf8")
        cur.execute(query)
        cur.execute(query1)
    cur.close()
    con.close()

    response_data = {}
    response_data['result'] = 'success'
    return HttpResponse(simplejson.dumps(response_data), mimetype='application/javascript')


def get_copykiller_result(request, course_id):
    con = mdb.connect(settings.DATABASES.get('default').get('HOST'), settings.DATABASES.get('default').get('USER'), settings.DATABASES.get('default').get('PASSWORD'), settings.DATABASES.get('default').get('NAME'));
    cur = con.cursor()
    query = "select "
    query += "v.student_id, "
    query += "v.report_id assessment_no, "
    query += "concat('http://pjsearch.kmooc.kr:8080/ckplus/copykiller.jsp?uri=', v.uri, '&property=0&lang=ko') total_link, "
    query += "concat('http://pjsearch.kmooc.kr:8080/ckplus/copykiller.jsp?uri=', v.uri, '&property=1&lang=ko') year_link, "
    query += "concat('http://pjsearch.kmooc.kr:8080/ckplus/copykiller.jsp?uri=', v.uri, '&property=2&lang=ko') term_link, "
    query += "concat('http://pjsearch.kmooc.kr:8080/ckplus/copykiller.jsp?uri=', v.uri, '&property=3&lang=ko') class_link, "
    query += "concat('http://pjsearch.kmooc.kr:8080/ckplus/copykiller.jsp?uri=', v.uri, '&property=4&lang=ko') report_link, "
    query += "concat('http://pjsearch.kmooc.kr:8080/ckplus/copykiller.jsp?uri=', v.uri, '&property=100&lang=ko') internet_link, "
    query += "(select r.disp_total_copy_ratio from tb_copykiller_copyratio r where r.uri=v.uri and r.check_type='total') total, "
    query += "(select r.disp_total_copy_ratio from tb_copykiller_copyratio r where r.uri=v.uri and r.check_type='year') year, "
    query += "(select r.disp_total_copy_ratio from tb_copykiller_copyratio r where r.uri=v.uri and r.check_type='term') term, "
    query += "(select r.disp_total_copy_ratio from tb_copykiller_copyratio r where r.uri=v.uri and r.check_type='class') class, "
    query += "(select r.disp_total_copy_ratio from tb_copykiller_copyratio r where r.uri=v.uri and r.check_type='report') report, "
    query += "(select r.disp_total_copy_ratio from tb_copykiller_copyratio r where r.uri=v.uri and r.check_type='internet') internet "
    query += "from "
    query += "vw_copykiller v "
    query += "where "
    query += "v.uri in (select uri from tb_copykiller_copyratio) "
    query += "order by assessment_no, student_id "
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    con.close()
    result_list = list()
    for row in rows:
        result_list.append(row[0:])
    return result_list


def copykiller_csv(request, course_id):
    result_list = get_copykiller_result(request, course_id)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="'+course_id+'.csv"'
    writer = csv.writer(response)
    writer.writerow(['student id', 'assessment no', 'total link', 'year link', 'term link', 'class link', 'report link', 'internet link', 'total', 'year', 'term', 'class', 'report', 'internet'])
    for value in result_list:
        writer.writerow(value)
    return response