"""Organizations views for use with Studio."""


from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.generic import View

from openedx.core.djangolib.js_utils import dump_js_escaped_json


class OrganizationListView(View):
    """View rendering organization list as json.

    This view renders organization list json which is used in org
    autocomplete while creating new course.
    """

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):  # lint-amnesty, pylint: disable=unused-argument
        """Returns organization list as json."""
        # EDUNEXT: Organizations list must not be visible for users, reason why an empty array is returned
        org_names_list = []
        return HttpResponse(dump_js_escaped_json(org_names_list), content_type='application/json; charset=utf-8')  # lint-amnesty, pylint: disable=http-response-with-content-type-json
