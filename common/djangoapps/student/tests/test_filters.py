"""
Test that various filters are fired for models in the student app.
"""
from django.test import override_settings
from openedx_filters.learning.enrollment import PreEnrollmentFilter
from openedx_filters import PipelineStep

from common.djangoapps.student.models import CourseEnrollment, EnrollmentNotAllowed
from common.djangoapps.student.tests.factories import UserFactory, UserProfileFactory

from openedx.core.djangolib.testing.utils import skip_unless_lms

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class TestEnrollmentPipelineStep(PipelineStep):
    """
    Utility function used when getting steps for pipeline.
    """

    def run(self, user, course_key, mode):  # pylint: disable=unused-argument, arguments-differ
        """Pipeline steps that changes mode to honor."""
        if mode == "no-id-professional":
            raise PreEnrollmentFilter.PreventEnrollment()
        return {"mode": "honor"}


@skip_unless_lms
class EnrollmentFiltersTest(ModuleStoreTestCase):
    """
    Tests for the Open edX Filters associated with the enrollment process through the enroll method.

    This class guarantees that the following filters are triggered during the user's enrollment:

    - PreEnrollmentFilter
    """

    def setUp(self):  # pylint: disable=arguments-differ
        super().setUp()
        self.course = CourseFactory.create()
        self.user = UserFactory.create(
            username="test",
            email="test@example.com",
            password="password",
        )
        self.user_profile = UserProfileFactory.create(user=self.user, name="Test Example")

    @override_settings(
        OPEN_EDX_FILTERS_CONFIG={
            "org.openedx.learning.course.enrollment.started.v1": {
                "pipeline": [
                    "common.djangoapps.student.tests.test_filters.TestEnrollmentPipelineStep",
                ],
                "fail_silently": False,
            },
        },
    )
    def test_enrollment_filter_executed(self):
        """
        Test whether the student enrollment filter is triggered before the user's
        enrollment process.

        Expected result:
            - PreEnrollmentFilter is triggered and executes TestEnrollmentPipelineStep.
            - The arguments that the receiver gets are the arguments used by the filter
            with the enrollment mode changed.
        """
        enrollment = CourseEnrollment.enroll(self.user, self.course.id, mode='audit')

        self.assertEqual('honor', enrollment.mode)

    @override_settings(
        OPEN_EDX_FILTERS_CONFIG={
            "org.openedx.learning.course.enrollment.started.v1": {
                "pipeline": [
                    "common.djangoapps.student.tests.test_filters.TestEnrollmentPipelineStep",
                ],
                "fail_silently": False,
            },
        },
    )
    def test_enrollment_filter_prevent_enroll(self):
        """
        Test prevent the user's enrollment through a pipeline step.

        Expected result:
            - PreEnrollmentFilter is triggered and executes TestEnrollmentPipelineStep.
            - The user can't enroll.
        """
        with self.assertRaises(EnrollmentNotAllowed):
            CourseEnrollment.enroll(self.user, self.course.id, mode='no-id-professional')
