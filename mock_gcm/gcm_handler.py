import json
import re
import urllib
import uuid

import cyclone.web
from twisted.logger import Logger


class GCMException(Exception):

    def __init__(self, msg="OK", status_code=200, detail=""):
        self.msg = msg
        self.status_code = status_code
        self.detail = detail

    def __str__(self):
        return "Error {}: {}".format(self.status_code, self.msg)


class GCMHandler(cyclone.web.RequestHandler):

    log = Logger()

    def check_headers(self, headers):
        try:
            auth = headers['authorization']
            if auth[:4] != 'key=':
                raise GCMException(
                    "InvalidAuthorizationHeader",
                    401,
                    "Invalid auth header specified. (missing 'key=')"
                )
        except KeyError:
            raise GCMException(
                "MissingAuthorization",
                401,
                "Authorization header is missing"
            )
        try:
            ctype = headers['content-type']
            if ctype.lower() not in ["application/json",
                                     "application/x-wwww-form-urlencoded;"
                                     "charset=UTF-8"]:
                raise GCMException("InvalidContentType",
                                   400,
                                   "Unknown Content-Type specified.")
        except KeyError:
            raise GCMException(
                "MissingContentType",
                400,
                "Content-Type Header missing"
            )
        if int(headers.get('content-length', 4096)) > 4096:
            raise GCMException(
                "MessageTooBig",
                200,
                "Message body exceeds 4096 bytes"
            )

    def parse_query(self, qs):  # type (str) -> typing.Dict
        result = {}
        for i in qs.split('&'):
            kv = urllib.unquote_plus(i).split('=', 1)
            value = True
            try:
                key = kv[0].strip("'").strip('"')
                value = kv[1]
            except IndexError:
                pass
            result[key] = value
        return result

    def load_body(self, type, body):
        invalid_keys = ["registration_ids", "collapse_key", "time_to_live",
                        "restricted_package_name", "dry_run", "data"]
        if (type.lower() == "application/json"):
            rbody = json.loads(body)
        else:
            rbody = self.parse_query(body)
        to = rbody.get('to')
        reg_ids = rbody.get('registration_ids')
        cond = rbody.get('condition')
        if reg_ids:
            if len(reg_ids) > 1000:
                raise GCMException("InvalidRegistration",
                                   200,
                                   "Too many registration_ids")
        if not (to or reg_ids or cond):
            raise GCMException("MissingRegistration",
                               200,
                               "Missing body field: registration_ids")
        if reg_ids and to:
            raise GCMException("MissingRegistration",
                               200,
                               "reg_ids and to present in payload")
        if cond and to:
            raise GCMException("InvalidRegistration",
                               200,
                               "condition and to present in payload")
        if cond and not re.match(
                "^('[^']+' in topics *(&&|\|\|)? *){1,2}$", cond):
            raise GCMException("InvalidRegistration",
                               200,
                               "condition is invalid")
        for k in rbody.get('data', {}):
            if (k[:4] == "from" or k[:3] == "gcm" or k[:3] == "fcm" or
                    k[:6] == "google" or k in invalid_keys):
                raise GCMException("InvalidDataKey",
                                   200,
                                   "An invalid keyword was specified in "
                                   "the data field.")

    @cyclone.web.asynchronous
    def post(self, *args, **kwargs):
        # header check
        response  = {
            "multicast_id": uuid.uuid4().hex,
            "success": 0,
            "failure": 0,
            "canonical_ids": 0,
            "results": [],
        }
        return_code = 200
        try:
            test_reply = self.request.headers.get("x-return")
            if test_reply:
                try:
                    code, reply = test_reply.split(' ', 1)
                    raise GCMException(
                        reply,
                        int(code),
                        "Custom response: {}".format(test_reply))
                except (AttributeError, ValueError) as e:
                    raise GCMException(
                        "InvalidXReturn",
                        400,
                        "X-Return should be \"{int} Message\" " + repr(e))
            self.check_headers(self.request.headers)
            self.load_body(
                self.request.headers["content-type"],
                self.request.body,
            )
            # post success
            response["success"] = 1
            response["results"] = ["message_id:{}".format(uuid.uuid4().hex)]
        except GCMException as e:
            self.log.error("{}{}".format(
                repr(e),
                "\n"+e.detail if e.detail else "",
            ))
            response["failure"] = 1
            response["results"] = ["error:{}".format(e.msg)]
            return_code = e.status_code

        self.set_status(return_code)
        self.write(json.dumps(response))
        self.finish()