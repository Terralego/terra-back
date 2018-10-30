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

        csv_builder.create_csv(output)
        csv_builder2.create_csv(output)
