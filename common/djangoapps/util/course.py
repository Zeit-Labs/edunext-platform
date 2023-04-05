"""
Utility methods related to course
"""


import logging
from urllib.parse import urlencode

from django.conf import settings
from opaque_keys.edx.keys import CourseKey, UsageKey

from openedx_filters.exceptions import OpenEdxFilterException
from openedx_filters.tooling import OpenEdxPublicFilter
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

log = logging.getLogger(__name__)

COURSE_SHARING_UTM_PARAMETERS = {
    'facebook': {
        'utm_medium': 'social',
        'utm_campaign': 'social-sharing-db',
        'utm_source': 'facebook',
    },
    'twitter': {
        'utm_medium': 'social',
        'utm_campaign': 'social-sharing-db',
        'utm_source': 'twitter',
    },
}


def get_encoded_course_sharing_utm_params():
    """
    Returns encoded Course Sharing UTM Parameters.
    """
    return {
        utm_source: urlencode(utm_params)
        for utm_source, utm_params in COURSE_SHARING_UTM_PARAMETERS.items()
    }


def get_link_for_about_page(course):
    """
    Arguments:
        course: This can be either a course overview object or a course descriptor.

    Returns the course sharing url, this can be one of course's social sharing url, marketing url, or
    lms course about url.
    """
    is_social_sharing_enabled = configuration_helpers.get_value(
        'SOCIAL_SHARING_SETTINGS',
        getattr(settings, 'SOCIAL_SHARING_SETTINGS', {})
    ).get('CUSTOM_COURSE_URLS')
    if is_social_sharing_enabled and course.social_sharing_url:
        course_about_url = course.social_sharing_url
    elif settings.FEATURES.get('ENABLE_MKTG_SITE') and getattr(course, 'marketing_url', None):
        course_about_url = course.marketing_url
    else:
        about_base = configuration_helpers.get_value('LMS_ROOT_URL', settings.LMS_ROOT_URL)

        try:
            ## .. filter_implemented_name: TenantAwareLinkRenderStarted
            ## .. filter_type: org.openedx.learning.tenant_aware_link.render.started.v1
            about_base = TenantAwareLinkRenderStarted.run_filter(
                context=about_base,
                org=course.id.org,
                val_name='LMS_ROOT_URL',
                default=settings.LMS_ROOT_URL
            )
        except TenantAwareLinkRenderStarted.PreventTenantAwarelinkRender as exc:
            raise TenantAwareRenderNotAllowed(str(exc)) from exc
        
        course_about_url = '{about_base_url}/courses/{course_key}/about'.format(
            about_base_url=about_base,
            course_key=str(course.id),
        )

    return course_about_url


class TenantAwareRenderException(Exception):
    pass


class TenantAwareRenderNotAllowed(TenantAwareRenderException):
    pass


class TenantAwareLinkRenderStarted(OpenEdxPublicFilter):
    """
    Custom class used to create tenant aware link render filters and its custom methods.
    """

    filter_type = "org.openedx.learning.tenant_aware_link.render.started.v1"

    class PreventTenantAwarelinkRender(OpenEdxFilterException):
        """
        Custom class used to stop tenant aware link render process.
        """

    @classmethod
    def run_filter(cls, context, org, val_name, default):
        """
        Execute a filter with the signature specified.
        Arguments:
        context (str): rendering context value
        org (str): Course org filter, this value will be used to filter out the correct tenant configuration.
        val_name (str): Name of the key for which to return configuration value.
        default: default value to return if key is not present in the configuration
        """
        data = super().run_pipeline(context=context, org=org, val_name=val_name, default=default)
        return data.get("context")


def has_certificates_enabled(course):
    """
    Arguments:
        course: This can be either a course overview object or a course descriptor.
    Returns a boolean if the course has enabled certificates
    """
    if not settings.FEATURES.get('CERTIFICATES_HTML_VIEW', False):
        return False
    return course.cert_html_view_enabled


def course_location_from_key(course_key: CourseKey) -> UsageKey:
    """Creates a usage key for the toplevel course item, handling differences between mongo and newer keys"""
    if getattr(course_key, 'deprecated', False):
        block_id = course_key.run
    else:
        block_id = 'course'
    return course_key.make_usage_key('course', block_id)
