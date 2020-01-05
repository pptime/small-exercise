import sys
import tornado.web
import tornado.ioloop
import tornado.httpserver
from tornado.options import define, options
from tornado.log import app_log
from tornado.concurrent import futures
import functools


# https://github.com/encode/django-rest-framework/blob
# /ebcd93163a5d0663d16a16d4691df1bbe965d42f/rest_framework/status.py
class Status:
    HTTP_100_CONTINUE = 100
    HTTP_101_SWITCHING_PROTOCOLS = 101
    HTTP_200_OK = 200
    HTTP_201_CREATED = 201
    HTTP_202_ACCEPTED = 202
    HTTP_203_NON_AUTHORITATIVE_INFORMATION = 203
    HTTP_204_NO_CONTENT = 204
    HTTP_205_RESET_CONTENT = 205
    HTTP_206_PARTIAL_CONTENT = 206
    HTTP_207_MULTI_STATUS = 207
    HTTP_208_ALREADY_REPORTED = 208
    HTTP_226_IM_USED = 226
    HTTP_300_MULTIPLE_CHOICES = 300
    HTTP_301_MOVED_PERMANENTLY = 301
    HTTP_302_FOUND = 302
    HTTP_303_SEE_OTHER = 303
    HTTP_304_NOT_MODIFIED = 304
    HTTP_305_USE_PROXY = 305
    HTTP_306_RESERVED = 306
    HTTP_307_TEMPORARY_REDIRECT = 307
    HTTP_308_PERMANENT_REDIRECT = 308
    HTTP_400_BAD_REQUEST = 400
    HTTP_401_UNAUTHORIZED = 401
    HTTP_402_PAYMENT_REQUIRED = 402
    HTTP_403_FORBIDDEN = 403
    HTTP_404_NOT_FOUND = 404
    HTTP_405_METHOD_NOT_ALLOWED = 405
    HTTP_406_NOT_ACCEPTABLE = 406
    HTTP_407_PROXY_AUTHENTICATION_REQUIRED = 407
    HTTP_408_REQUEST_TIMEOUT = 408
    HTTP_409_CONFLICT = 409
    HTTP_410_GONE = 410
    HTTP_411_LENGTH_REQUIRED = 411
    HTTP_412_PRECONDITION_FAILED = 412
    HTTP_413_REQUEST_ENTITY_TOO_LARGE = 413
    HTTP_414_REQUEST_URI_TOO_LONG = 414
    HTTP_415_UNSUPPORTED_MEDIA_TYPE = 415
    HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE = 416
    HTTP_417_EXPECTATION_FAILED = 417
    HTTP_418_IM_A_TEAPOT = 418
    HTTP_422_UNPROCESSABLE_ENTITY = 422
    HTTP_423_LOCKED = 423
    HTTP_424_FAILED_DEPENDENCY = 424
    HTTP_426_UPGRADE_REQUIRED = 426
    HTTP_428_PRECONDITION_REQUIRED = 428
    HTTP_429_TOO_MANY_REQUESTS = 429
    HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE = 431
    HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS = 451
    HTTP_500_INTERNAL_SERVER_ERROR = 500
    HTTP_501_NOT_IMPLEMENTED = 501
    HTTP_502_BAD_GATEWAY = 502
    HTTP_503_SERVICE_UNAVAILABLE = 503
    HTTP_504_GATEWAY_TIMEOUT = 504
    HTTP_505_HTTP_VERSION_NOT_SUPPORTED = 505
    HTTP_506_VARIANT_ALSO_NEGOTIATES = 506
    HTTP_507_INSUFFICIENT_STORAGE = 507
    HTTP_508_LOOP_DETECTED = 508
    HTTP_509_BANDWIDTH_LIMIT_EXCEEDED = 509
    HTTP_510_NOT_EXTENDED = 510
    HTTP_511_NETWORK_AUTHENTICATION_REQUIRED = 511


@tornado.web.stream_request_body
class ArrayStreamHandler(tornado.web.RequestHandler):
    """
    Stream based REST api
    Upload a list of integer in json format being processed on the fly

    """

    def initialize(self, executor=None):
        self.sum = 0
        self.buffer = ""
        self.error = ""
        self.opening = None
        self.executor = executor

    def parse_and_sum(self, chunk):
        try:
            for c in chunk.decode():
                if c == "[":
                    if self.opening is None:
                        self.opening = True
                    else:
                        self.error = "input format must be a list of integers in json format"
                elif c == "]":
                    if self.opening:
                        self.opening = False
                    else:
                        self.error = "input format must be a list of integers in json format"
                elif c == ",":
                    if self.buffer.strip():
                        num = int(self.buffer.strip())
                        self.sum += num
                    self.buffer = ""
                else:
                    self.buffer += c
        except ValueError:
            self.error = "input format must be a list of integers in json format"

    def finish_computation(self):
        try:
            if self.buffer.strip():
                num = int(self.buffer.strip())
                self.sum += num
                self.buffer = ""
        except ValueError:
            self.error = "input format must be a list of integers in json format"
        if self.error:
            self.set_status(Status.HTTP_400_BAD_REQUEST)
            self.write(
                {
                    "error": self.error
                }
            )
        else:
            if self.opening is False:
                self.set_status(Status.HTTP_201_CREATED)
                self.write(
                    {
                        "total": self.sum
                    }
                )
            else:
                self.set_status(Status.HTTP_400_BAD_REQUEST)
                self.write(
                    {
                        "total": self.sum,
                        "warning": "input format must be a list of integers in json format, missing closing bracket"
                    }
                )

    async def data_received(self, chunk: bytes):
        """
        The stream is a list of integer in json format
        :param chunk:
        :return:
        """
        await tornado.ioloop.IOLoop.instance().run_in_executor(executor=self.executor,
                                                               func=functools.partial(self.parse_and_sum, chunk))

    async def post(self, *args, **kwargs):
        app_log.debug("data receiving finished")
        await tornado.ioloop.IOLoop.instance().run_in_executor(executor=self.executor,
                                                               func=self.finish_computation)


def make_app(debug=True,
             thread_num=None):
    """
    Make the application
    :param debug: make the application in debug mode
    :return: application
    """

    routes_list = list()
    routes_list.append((r'/total/', ArrayStreamHandler,
                        dict(executor=futures.ThreadPoolExecutor(max_workers=thread_num))))
    return tornado.web.Application(
        routes_list,
        debug=debug
    )


def start_server(http_address="",
                 http_port=8000,
                 thread_num=None
                 ):
    """
    Start http server
    :param enable_http: enable http end point
    :param http_address: the http address to listen to
    :param http_port: the http port to listen to
    :param thread_num: the number of threads allowed per process
    :return:
    """

    app = make_app(debug=options.app_debug,
                   thread_num=thread_num)

    app_log.info('starting http server on {}:{}'.format(
        http_address,
        http_port
    ))

    http_server = tornado.httpserver.HTTPServer(app)
    http_server.bind(http_port, address=http_address,
                     backlog=options.http_backlog_size)

    if options.enable_auto_fork:
        http_server.start(0)
    else:
        http_server.start()

    io_loop = tornado.ioloop.IOLoop.instance()

    io_loop.start()


def setup_options():
    http_group = "http"
    application = "application"

    define("enable-auto-fork", default=False,
           type=bool, help="enable vertical autoscaling"
           )
    define("thread-num",
           type=int,
           default=None,
           help="number of threads per process")
    define("app-debug",
           default=False,
           type=bool,
           help='make application in debug mode',
           group=application)
    define('http-address',
           default="",
           group=http_group,
           help="http address")
    define('http-port',
           default=8000,
           type=int,
           group=http_group,
           help='http port')
    define('http-backlog-size',
           group=http_group,
           default=150,
           type=int,
           help='http server backlog size')


def verify_options():
    if sys.platform == "win32":
        raise tornado.options.Error(
            "auto-fork is incompatible with Windows"
        )


def main():
    setup_options()
    tornado.options.parse_command_line()
    verify_options()
    start_server(
        http_address=options.http_address,
        http_port=options.http_port,
        thread_num=options.thread_num
    )


if __name__ == '__main__':
    main()
