import json
from tornado.testing import AsyncHTTPTestCase, gen_test
from sum_calculator.server import make_app


class TestSumCalculator(AsyncHTTPTestCase):

    def get_app(self):
        return make_app(debug=True)

    def test_compute_normal(self):
        response = self.fetch('/total/', method="POST", body=json.dumps(
            list(range(101))
        ))
        self.assertEqual(response.code, 201)
        self.assertEqual(response.body, b'{"total": 5050}')

    def test_compute_big(self):
        response = self.fetch('/total/', method="POST", body=json.dumps(
            list(range(100001))
        ))
        self.assertEqual(response.code, 201)
        self.assertEqual(response.body, b'{"total": 5000050000}')

    @gen_test
    def test_compute_big_concurrent(self):
        resp1, resp2, resp3, resp4 = yield [
            self.http_client.fetch(self.get_url('/total/'), method="POST", body=json.dumps(
                list(range(100001))
            )),
            self.http_client.fetch(self.get_url('/total/'), method="POST", body=json.dumps(
                list(range(100002))
            )),
            self.http_client.fetch(self.get_url('/total/'), method="POST", body=json.dumps(
                list(range(100001))
            )),
            self.http_client.fetch(self.get_url('/total/'), method="POST", body=json.dumps(
                list(range(100002))
            )),
        ]
        self.assertEqual(resp1.code, 201)
        self.assertEqual(resp1.body, b'{"total": 5000050000}')
        self.assertEqual(resp2.code, 201)
        self.assertEqual(resp2.body, b'{"total": 5000150001}')
        self.assertEqual(resp3.code, 201)
        self.assertEqual(resp3.body, b'{"total": 5000050000}')
        self.assertEqual(resp4.code, 201)
        self.assertEqual(resp4.body, b'{"total": 5000150001}')

    def test_atypical_format_indentation(self):
        json_with_indentation = self.fetch('/total/', method="POST", body=json.dumps(
            list(range(100001)), indent=4
        ))
        self.assertEqual(json_with_indentation.code, 201)
        self.assertEqual(json_with_indentation.body, b'{"total": 5000050000}')

    def test_atypical_format_handwritten(self):
        hand_written_format = self.fetch('/total/', method="POST", body="[1, \r\n, 2 \r, 3 \t, \n4\n]")
        self.assertEqual(hand_written_format.code, 201)
        self.assertEqual(hand_written_format.body, b'{"total": 10}')

    def test_bad_format_missing_closing_bracket(self):
        hand_written_format = self.fetch('/total/', method="POST", body="[1, \r\n, 2 \r, 3 \t, \n4\n")
        self.assertEqual(hand_written_format.code, 400)
        self.assertEqual(hand_written_format.body,
                         b'{"total": 10, "warning": "input format must be a list of integers in json fo'
                         b'rmat, missing closing bracket"}')

    def test_bad_format(self):
        hand_written_format = self.fetch('/total/', method="POST", body="[1, \r\n, t2 \r, 3 \t, \n4\n")
        self.assertEqual(hand_written_format.code, 400)
        self.assertEqual(hand_written_format.body,
                         b'{"error": "input format must be a list of integers in json fo'
                         b'rmat"}')
