from collections import namedtuple
from datetime import datetime

from dimagi.utils.dates import DateSpan
from dimagi.utils.decorators.memoized import memoized


class FilterException(Exception):
    pass


class MissingParamException(FilterException):
    pass


class FilterValueException(FilterException):
    pass


FilterParam = namedtuple('FilterParam', ['name', 'required'])


class BaseFilter(object):
    """
    Base object for filters.
    """

    def __init__(self, name, required=False, params=None):
        self.name = name
        self.required = required
        self.params = params or []

    def get_value(self, context):
        context_ok = self.check_context(context)
        if self.required and not context_ok:
            required_slugs = ', '.join([slug.name for slug in self.params if slug.required])
            raise MissingParamException("Missing filter parameters. "
                                        "Required parameters are: {}".format(required_slugs))

        if context_ok:
            kwargs = {param.name: context[param.name] for param in self.params if param.name in context}
            return self.value(**kwargs)
        else:
            return self.default_value()

    def check_context(self, context):
        return all(slug.name in context for slug in self.params if slug.required)

    def value(self, **kwargs):
        """
        Override this and return the value. This method will only be called if all required
        parameters are present in the filter context. All the parameters present in the context
        will be passed in as keyword arguments.

        If any of the parameters are invalid a FilterValueException should be raised.

        This method should generally be memoized.
        """
        return None

    def default_value(self):
        """
        If the filter is not marked as required and the user does not supply any / all necessary parameters
        this value will be used instead.
        """
        return None

    def context(self, value):
        """
        Context for rendering the filter.
        """
        context = {
            'label': self.label,
            'css_id': self.css_id,
            'value': value,
        }
        context.update(self.filter_context())
        return context

    def filter_context(self):
        """
        Override to supply additional context.
        """
        return {}


class DatespanFilter(BaseFilter):

    def __init__(self, name, required=True, label='Datespan Filter',
                 template='reports_core/filters/datespan_filter.html',
                 css_id=None):
        # todo: should these be in the constructor as well?
        params = [
            FilterParam('startdate', True),
            FilterParam('enddate', True),
            FilterParam('date_range_inclusive', False),
        ]
        super(DatespanFilter, self).__init__(required=required, name=name, params=params)
        self.label = label
        self.template = template
        self.css_id = css_id or self.name

    @memoized
    def value(self, startdate, enddate, date_range_inclusive=True):
        def date_or_nothing(param):
            return datetime.strptime(param, "%Y-%m-%d") \
                if param else None
        try:
            startdate = date_or_nothing(startdate)
            enddate = date_or_nothing(enddate)
        except (ValueError, TypeError) as e:
            raise FilterValueException('Error parsing date parameters: {}'.format(e.message))

        if startdate or enddate:
            return DateSpan(startdate, enddate, inclusive=date_range_inclusive)

    def default_value(self):
        # default to a week's worth of data.
        return DateSpan.since(7)

    def filter_context(self):
        return {
            'timezone': None
        }


Choice = namedtuple('Choice', ['value', 'display'])


class ChoiceListFilter(BaseFilter):
    """
    Filter for a list of choices. Each choice should be a Choice object as per above.
    """

    def __init__(self, name, required=True, label='Choice List Filter',
                 template='reports_core/filters/choice_list_filter.html',
                 css_id=None, choices=None):
        params = [
            FilterParam(name, True),
        ]
        super(ChoiceListFilter, self).__init__(required=required, name=name, params=params)
        self.label = label
        self.template = template
        self.css_id = css_id or self.name
        self.choices = choices or []

    def value(self, **kwargs):
        choice = kwargs[self.name]
        return next(choice_obj for choice_obj in self.choices if choice_obj.value == choice)

    def default_value(self):
        return self.choices[0]
