import datetime

from django.test import TestCase

import ew.models as models
import ew.views as views

class DateHandlingTest(TestCase):

    def test_date_handling(self):
        dt = datetime.datetime
        date = datetime.date
        self.assertFalse(
            models.is_word_due(
                date(2011, 1, 10),
                models.get_user_time(timezone=2,
                                     turning_point=3 * 60,
                                     now=dt(2011, 1, 10, 0, 59))))
        self.assertTrue(
            models.is_word_due(
                date(2011, 1, 10),
                models.get_user_time(timezone=2,
                                     turning_point=3 * 60,
                                     now=dt(2011, 1, 10, 1, 0))))
        self.assertTrue(
            models.is_word_due(
                date(2011, 1, 10),
                models.get_user_time(timezone=2,
                                     turning_point=3 * 60,
                                     now=dt(2011, 1, 10, 1, 1))))

    def test_view(self):

        self.assertEqual(
            views.remove_query_param('a.com/b?c=1&d=2&e=3', 'd'),
            'a.com/b?c=1&e=3')

        self.assertEqual(
            views.remove_query_param('a.com/b?c=1&d=2&e=3', 'x'),
            'a.com/b?c=1&d=2&e=3')

        self.assertEqual(
            views.remove_query_param('a.com/b?c=ű&ő=1&ű=ő', 'ő'),
            'a.com/b?c=%C5%B1&%C5%B1=%C5%91')
