import json

from cyclone.web import Application
from mock import Mock
from mock_gcm.gcm_handler import GCMHandler, GCMException
from twisted.internet.defer import Deferred
from twisted.trial import unittest
from nose.tools import eq_, ok_, assert_raises

class GCMExceptionTestACase(unittest.TestCase):

    def test_exception(self):
        ex = GCMException()
        eq_(str(ex), "Error 200: OK")


class GCMTestCase(unittest.TestCase):

    def setUp(self):
        self.body = json.dumps({"registration_ids": ["1234"],
                                "data": {}})
        self.headers = {
            "content-type": "application/json",
            "authorization": "key=authvalue",
            "content-length": len(self.body),
        }
        self.request_mock = Mock(headers=self.headers,
                                 body=self.body)
        self.handler = GCMHandler(Application(),
                                  self.request_mock)
        self.write_mock = self.handler.write = Mock()
        self.status_mock = self.handler.set_status = Mock()
        self.finish_deferred = Deferred()
        self.handler.finish = lambda: self.finish_deferred.callback(True)

    def set_payload(self, payload):
        self.body = json.dumps(payload)
        self.headers['content-length'] = len(self.body)

    def test_check_headers_ok(self):
        self.handler.check_headers(self.headers)

    def test_check_headers_no_auth(self):
        del(self.headers['authorization'])
        with assert_raises(GCMException) as ex:
            self.handler.check_headers(self.headers)
        eq_(ex.exception.status_code, 401)

    def test_check_headers_no_auth_key(self):
        self.headers['authorization'] = "invalid"
        with assert_raises(GCMException) as ex:
            self.handler.check_headers(self.headers)
        eq_(ex.exception.status_code, 401)
        eq_(ex.exception.msg, "MissingAuthorization")

    def test_check_headers_no_auth_key(self):
        self.headers['authorization'] = "invalid"
        with assert_raises(GCMException) as ex:
            self.handler.check_headers(self.headers)
        eq_(ex.exception.status_code, 401)
        eq_(ex.exception.msg, "InvalidAuthorizationHeader")

    def test_check_headers_bad_content(self):
        self.headers['content-type'] = "invalid"
        with assert_raises(GCMException) as ex:
            self.handler.check_headers(self.headers)
        eq_(ex.exception.status_code, 400)
        eq_(ex.exception.msg, "InvalidContentType")

    def test_check_headers_missing_content(self):
        del(self.headers['content-type'])
        with assert_raises(GCMException) as ex:
            self.handler.check_headers(self.headers)
        eq_(ex.exception.status_code, 400)
        eq_(ex.exception.msg, "MissingContentType")

    def test_check_headers_too_much_content(self):
        self.headers['content-length'] = '8000'
        with assert_raises(GCMException) as ex:
            self.handler.check_headers(self.headers)
        eq_(ex.exception.status_code, 200)
        eq_(ex.exception.msg, "MessageTooBig")

    def test_load_body_ok(self):
        self.handler.load_body("application/json", self.body)

    def test_load_body_no_regs(self):
        self.set_payload(
            {
                "registration_ids": [],
                "data": {},
            }
        )
        with assert_raises(GCMException) as ex:
            self.handler.load_body("application/json", self.body)
        eq_(ex.exception.status_code, 200)
        eq_(ex.exception.msg, "MissingRegistration")

    def test_load_body_too_many_regs(self):
        regs = [str(i) for i in range(0, 1001)]
        self.set_payload(
            {
                "registration_ids": regs,
                "data": {},
            }
        )
        with assert_raises(GCMException) as ex:
            self.handler.load_body("application/json", self.body)
        eq_(ex.exception.status_code, 200)
        eq_(ex.exception.msg, "InvalidRegistration")

    def test_load_body_to_and_reg(self):
        self.set_payload(
            {
                "to": "123",
                "registration_ids": ["123"],
                "data": {}
            }
        )
        with assert_raises(GCMException) as ex:
            self.handler.load_body("application/json", self.body)
        eq_(ex.exception.status_code, 200)
        eq_(ex.exception.msg, "MissingRegistration")

    def test_load_body_cond_and_to(self):
        self.set_payload(
            {
                "to": "123",
                "condition": "'foo' in topics",
                "data": {}
            }
        )
        with assert_raises(GCMException) as ex:
            self.handler.load_body("application/json", self.body)
        eq_(ex.exception.status_code, 200)
        eq_(ex.exception.msg, "InvalidRegistration")

    def test_load_body_bad_cond(self):
        self.set_payload(
            {
                "condition": "foo in topics",
                "data": {}
            }
        )
        with assert_raises(GCMException) as ex:
            self.handler.load_body("application/json", self.body)
        eq_(ex.exception.status_code, 200)
        eq_(ex.exception.msg, "InvalidRegistration")

    def test_load_body_bad_data(self):
        self.set_payload(
            {
                "to": "123",
                "data": {
                    "dry_run": False
                }
            }
        )
        with assert_raises(GCMException) as ex:
            self.handler.load_body("application/json", self.body)
        eq_(ex.exception.status_code, 200)
        eq_(ex.exception.msg, "InvalidDataKey")

    def test_parse_query(self):
        self.body="alpha=beta&gamma=delta&epsilon"
        result = self.handler.parse_query(self.body)
        eq_(result, {'alpha': 'beta', 'gamma': 'delta', 'epsilon': True})

    def test_load_body_query(self):
        self.body="to='123'"
        self.handler.load_body("application/x-www-form-urlencoded;"
                               "charset=UTF-8", self.body)

    def test_post(self):
        self.handler.post()
        return self.finish_deferred

    def test_post_return(self):
        self.headers.update({"x-return": "200 ok"})

        def handle_finish(*args):
            args = json.loads(self.write_mock.call_args[0][0])
            eq_(args['results'], ["error:ok"])
            eq_(self.status_mock.call_args[0][0], 200)

        self.finish_deferred.addCallback(handle_finish)
        self.handler.post()
        return self.finish_deferred

    def test_post_bad_return(self):
        self.headers.update({"x-return": "invalid"})

        def handle_finish(*args):
            args = json.loads(self.write_mock.call_args[0][0])
            eq_(args['results'], ["error:InvalidXReturn"])
            eq_(self.status_mock.call_args[0][0], 400)

        self.finish_deferred.addCallback(handle_finish)
        self.handler.post()

        return self.finish_deferred

    def bottom(self):
        pass