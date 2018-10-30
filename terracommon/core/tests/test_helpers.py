from io import StringIO

from django.test import TestCase

from terracommon.core.helpers import CustomCsvBuilder


class CSVTestCase(TestCase):
    def test_create_csv(self):
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
        data2 = {"test": "hello-world", "test2": "HELLO-WORLD"}

        csv_builder = CustomCsvBuilder(data)
        csv_builder2 = CustomCsvBuilder(data2)
        output = StringIO()
        output2 = StringIO()
        csv_builder.create_csv(output)
        list_lines = self.get_columns(output.read())
        self.assertEqual(sorted(list(zip(list_lines[0],
                                         list_lines[1],
                                         list_lines[2]
                                         ))),
                         [('test', 'hello-world', ''),
                          ('value', '', ''),
                          ('value_data_test0_fourth_events', '', '1'),
                          ('value_data_test0_fourth_participants', '', '1'),
                          ('value_data_test1_first_events', '1', '1'),
                          ('value_data_test1_first_participants', '1', '1'),
                          ('value_data_test1_second_events', '2', '8'),
                          ('value_data_test1_second_participants', '2', '73'),
                          ('value_data_test1_third_events', '1', '1'),
                          ('value_data_test1_third_participants', '101',
                           '101'),
                          ('value_name', 'Name1', 'Name2')])

        csv_builder2.create_csv(output2)
        list_lines2 = self.get_columns(output2.read())
        self.assertEqual(sorted(list(zip(list_lines2[0],
                                         list_lines2[1],
                                         ))),
                         [('test', 'hello-world'),
                          ('test2', 'HELLO-WORLD')])

    def get_columns(self, csv):
        list_csv = []
        tab = csv.split('\r\n')
        tab.pop(-1)
        for line in tab:
            values = line.split(',')
            list_csv.append(values)
        return list_csv
