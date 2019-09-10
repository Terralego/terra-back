from io import StringIO

from django.test import TestCase

from terracommon.core.helpers import Choices, CustomCsvBuilder


class CSVTestCase(TestCase):
    def test_create_csv_1(self):
        data = {"test": "hello-world",
                "value": [
                    {"data": {
                        "test1": {
                            "first": {
                                "events": 1,
                                "participants": 1},
                            "second": {
                                "events": 2,
                                "participants": 2},
                            "third": {
                                "events": 1,
                                "participants": 101}
                                   }
                              },
                     "name": "Name1"
                     },
                    {"data": {
                        "test0": {
                            "fourth": {
                                "events": 1,
                                "participants": 1
                            }
                        },
                        "test1": {
                            "first": {
                                "events": 1,
                                "participants": 1
                            },
                            "second": {
                                "events": 8,
                                "participants": 73
                            },
                            "third": {
                                "events": 1,
                                "participants": 101}
                        }
                    },
                        "name": "Name2"}
                ]
                }

        csv_builder = CustomCsvBuilder(data)

        output = StringIO()
        csv_builder.create_csv(output)
        list_lines = self.get_columns(output.read())
        self.assertCountEqual(
            list_lines,
            [['test', 'hello-world', ''],
             ['value', '', ''],
             ['value_data_test0_fourth_events', '', '1'],
             ['value_data_test0_fourth_participants', '', '1'],
             ['value_data_test1_first_events', '1', '1'],
             ['value_data_test1_first_participants', '1', '1'],
             ['value_data_test1_second_events', '2', '8'],
             ['value_data_test1_second_participants', '2', '73'],
             ['value_data_test1_third_events', '1', '1'],
             ['value_data_test1_third_participants', '101', '101'],
             ['value_name', 'Name1', 'Name2']])

    def test_create_csv_2(self):
        data = {"test": "hello-world", "test2": "HELLO-WORLD"}
        csv_builder = CustomCsvBuilder(data)
        output = StringIO()
        csv_builder.create_csv(output)
        list_lines = self.get_columns(output.read())
        self.assertCountEqual(
            list_lines,
            [['test', 'hello-world'], ['test2', 'HELLO-WORLD']])

    def get_columns(self, csv):
        list_csv = []
        tab = csv.split('\r\n')
        tab.pop(-1)
        for line in tab:
            values = line.split(',')
            list_csv.append(values)
        by_column = []
        for id in range(len(list_csv[0])):
            column = []
            for line in list_csv:
                column.append(line[id])
            by_column.append(column)
        return by_column


class ChoicesTests(TestCase):
    def setUp(self):
        self.MY_CHOICES = Choices(
            ('ONE', 1, 'One for the money'),
            ('TWO', 2, 'Two for the show'),
            ('THREE', 3, 'Three to get ready'),
        )
        self.MY_CHOICES.add_subset("ODD", ("ONE", "THREE"))

    """
    Testing the choices
    """
    def test_simple_choice(self):
        self.assertEqual(self.MY_CHOICES.CHOICES,
                         ((1, "One for the money"),
                          (2, "Two for the show"),
                          (3, "Three to get ready"),))
        self.assertEqual(self.MY_CHOICES.CHOICES_DICT,
                         {
                             1: 'One for the money',
                             2: 'Two for the show',
                             3: 'Three to get ready'
                         })
        self.assertEqual(self.MY_CHOICES.REVERTED_CHOICES_DICT,
                         {
                             'One for the money': 1,
                             'Three to get ready': 3,
                             'Two for the show': 2
                         })

    def test__contains__(self):
        self.failUnless(self.MY_CHOICES.ONE in self.MY_CHOICES)

    def test__iter__(self):
        self.assertEqual([k for k, v in self.MY_CHOICES], [1, 2, 3])

    def test_unique_values(self):
        self.assertRaises(ValueError, Choices,
                          ('TWO', 4, 'Deux'), ('FOUR', 4, 'Quatre'))

    def test_unique_constants(self):
        self.assertRaises(ValueError, Choices,
                          ('TWO', 2, 'Deux'), ('TWO', 4, 'Quatre'))

    def test_const_choice(self):
        self.assertEqual(self.MY_CHOICES.CONST_CHOICES,
                         (("ONE", "One for the money"),
                          ("TWO", "Two for the show"),
                          ("THREE", "Three to get ready"),))

    def test_value_to_const(self):
        self.assertEqual(self.MY_CHOICES.VALUE_TO_CONST,
                         {1: "ONE", 2: "TWO", 3: "THREE"})

    def test_add_should_add_in_correct_order(self):
        SOME_CHOICES = Choices(
            ('ONE', 1, 'One'),
            ('TWO', 2, 'Two'),
        )
        OTHER_CHOICES = Choices(
            ('THREE', 3, 'Three'),
            ('FOUR', 4, 'Four'),
        )
        # Adding a choices to choices
        tup = SOME_CHOICES + OTHER_CHOICES
        self.assertEqual(tup, ((1, 'One'), (2, 'Two'),
                               (3, 'Three'), (4, 'Four')))

        # Adding a tuple to choices
        tup = SOME_CHOICES + ((3, 'Three'), (4, 'Four'))
        self.assertEqual(tup, ((1, 'One'), (2, 'Two'),
                               (3, 'Three'), (4, 'Four')))

        """Adding a choices to tuple => do not work; is it possible to
           emulate it?
            tup = ((1, 'One'), (2, 'Two')) + OTHER_CHOICES
            self.assertEqual(tup, ((1, 'One'), (2, 'Two'),
                                   (3, 'Three'), (4, 'Four')))
        """

    def test_retrocompatibility(self):
        MY_CHOICES = Choices(
            ('TWO', 2, 'Deux'),
            ('FOUR', 4, 'Quatre'),
            name="EVEN"
        )
        MY_CHOICES.add_choices("ODD",
                               ('ONE', 1, 'Un'),
                               ('THREE', 3, 'Trois'),)
        self.assertEqual(MY_CHOICES.CHOICES, ((2, 'Deux'), (4, 'Quatre'),
                                              (1, 'Un'), (3, 'Trois')))
        self.assertEqual(MY_CHOICES.ODD, ((1, 'Un'), (3, 'Trois')))
        self.assertEqual(MY_CHOICES.EVEN, ((2, 'Deux'), (4, 'Quatre')))


class SubsetTests(TestCase):
    def setUp(self):
        self.MY_CHOICES = Choices(
            ('ONE', 1, 'One for the money'),
            ('TWO', 2, 'Two for the show'),
            ('THREE', 3, 'Three to get ready'),
        )
        self.MY_CHOICES.add_subset("ODD", ("ONE", "THREE"))
        self.MY_CHOICES.add_subset("ODD_BIS", ("ONE", "THREE"))

    def test_basic(self):
        self.assertEqual(self.MY_CHOICES.ODD, ((1, 'One for the money'),
                                               (3, 'Three to get ready')))

    def test__contains__(self):
        self.failUnless(self.MY_CHOICES.ONE in self.MY_CHOICES.ODD)

    def test__eq__(self):
        self.assertEqual(self.MY_CHOICES.ODD, ((1, 'One for the money'),
                                               (3, 'Three to get ready')))
        self.assertEqual(self.MY_CHOICES.ODD, self.MY_CHOICES.ODD_BIS)
