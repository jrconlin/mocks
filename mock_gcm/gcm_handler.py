import json
import urllib
import uuid

import cyclone.web
from twisted.logger import Logger
from twisted.python import failure

class GCMException(Exception):

    def __init__(self, msg="OK", status_code=200, detail=""):
        self.msg = msg
        self.status_code = status_code
        self.log.error(detail)

    def __str__(self):
        return "Error {}: {}".format(self.status_code, self.msg)


class GCMHandler(cyclone.web.RequestHandler):

    log = Logger()

    def check_headers(self):
        try:
            auth = self.request.headers['authorization']
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
            ctype = self.request.headers['content-type']
            if ctype.lower() not in ["application/json",
                                     "application/x-wwww-form-urlencoded;"
                                     "charset=UTF-8"]:
                raise GCMException("InvalidContentType",
                                   400,
                                   "Unknown Content-Type specified.")
        except KeyError:
            self.log.error()
            raise GCMException(
                "MissingContentType",
                400,
                "Content-Type Header missing"
            )
        if self.requests.headers.get('content-length', 4096) > 4096:
            self.log.error()
            raise GCMException(
                "MessageTooBig",
                200,
                "Message body exceeds 4096 bytes"
            )

    def load_text(self, body):
        pass

    def load_json(self, body):
        pass

    def parse_query(self, qs):
        result = {}
        for i in qs.split('&'):
            kv = urllib.unquote_plus(i).split('=', 1)
            value = None
            try:
                key = kv[0].strip("'").strip('"')
                value = kv[1]
            except IndexError:
                pass
            result[key] = value
        return result

    def load_body(self):
        invalid_keys = ["registration_id", "collapse_key", "time_to_live",
                        "restricted_package_name", "dry_run", "data"]
        if (self.request.headers["content-type"].lower() is
                "application/json"):
            body = self.request.json()
        else:
            body = self.parse_query(self.request.content())
        if not body.get('registration_ids'):
            raise GCMException("MissingRegistration",
                               401,
                               "Missing body field: registration_ids")
        for k in body.data:
            if (k[:4] == "from" or k[:3] == "gcm" or k[:6] == "google" or
                    k in invalid_keys):
                raise GCMException("InvalidDataKey",
                                   200,
                                   "An invalid keyword was specified in "
                                   "the data field.")

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
            self.check_headers()
            self.load_body()
            # post success
            response["success"] = 1
            response["results"] = ["message_id:{}".format(uuid.uuid4().hex)]
        except GCMException as e:
            response["failure"] = 1
            response["results"] = ["error:{}".format(e.msg)]
            return_code = e.status_code

        self.set_status(return_code)
        self.write(json.dumps(response))