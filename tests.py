"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

import datetime

from django.test import TestCase

import ExponWords.ew.models as models

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
