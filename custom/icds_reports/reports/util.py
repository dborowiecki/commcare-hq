from __future__ import absolute_import

import abc

import six
from datetime import datetime

from custom.icds_reports.utils import get_age_filter


class FiltersContext(six.with_metaclass(abc.ABCMeta)):

    @abc.abstractmethod
    def get_filter_data(self, request_params):
        """

        Args:
            request_params (django.utils.datastructures.MultiValueDict)
        Returns:
            dict
        """
        pass


class LocationAndDateFilterContext(FiltersContext):

    def get_filter_data(self, request_params):
        include_test = request_params.get('include_test', False)
        now = datetime.utcnow()
        month = int(request_params.get('month', now.month))
        year = int(request_params.get('year', now.year))
        test_date = datetime(year, month, 1)

        location = request_params.get('location_id', '')
        return {
            'location_id': location,
            'date': test_date,
            'include_test': include_test
        }


class AllFiltersContext(FiltersContext):

    def get_filter_data(self, request_params):
        include_test = request_params.get('include_test', False)
        now = datetime.utcnow()
        month = int(request_params.get('month', now.month))
        year = int(request_params.get('year', now.year))
        test_date = datetime(year, month, 1)

        location = request_params.get('location_id', '')

        gender = request_params.get('gender', None)
        age = request_params.get('age', None)

        additional_filters = {}
        if gender:
            additional_filters.update({'gender': gender})
        if age:
            additional_filters.update(get_age_filter(age))

        return {
            'location_id': location,
            'date': test_date,
            'include_test': include_test,
            'additional_filters': additional_filters
        }
