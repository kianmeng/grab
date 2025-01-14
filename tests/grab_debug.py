import os
import threading

from mock import patch
from test_server import Response

from grab import Grab
from grab import base

from tests.util import BaseGrabTestCase
from tests.util import build_grab, temp_dir
from tests.util import reset_request_counter


class TestCookies(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_log_option(self):
        with temp_dir() as tmp_dir:
            reset_request_counter()

            log_file_path = os.path.join(tmp_dir, "lograb.html")
            grab = build_grab()
            grab.setup(log_file=log_file_path)
            self.server.add_response(Response(data=b"omsk"))

            self.assertEqual(os.listdir(tmp_dir), [])
            grab.go(self.server.get_url())
            self.assertEqual(os.listdir(tmp_dir), ["lograb.html"])
            with open(log_file_path, encoding="utf-8") as inp:
                self.assertEqual(inp.read(), "omsk")

    def test_log_dir_option(self):
        with temp_dir() as tmp_dir:
            reset_request_counter()

            grab = build_grab()
            grab.setup(log_dir=tmp_dir)
            self.server.add_response(Response(data=b"omsk1"))
            self.server.add_response(Response(data=b"omsk2"))

            self.assertEqual(os.listdir(tmp_dir), [])
            grab.go(self.server.get_url())
            grab.go(self.server.get_url())
            self.assertEqual(
                sorted(os.listdir(tmp_dir)), ["01.html", "01.log", "02.html", "02.log"]
            )
            with open(os.path.join(tmp_dir, "01.html"), encoding="utf-8") as inp:
                self.assertEqual(inp.read(), "omsk1")
            with open(os.path.join(tmp_dir, "02.html"), encoding="utf-8") as inp:
                self.assertEqual(inp.read(), "omsk2")

    def test_log_dir_response_content(self):
        with temp_dir() as tmp_dir:
            reset_request_counter()

            grab = build_grab()
            grab.setup(log_dir=tmp_dir)
            self.server.add_response(
                Response(data=b"omsk", headers=[("X-Engine", "PHP")])
            )

            self.assertEqual(os.listdir(tmp_dir), [])
            grab.go(self.server.get_url())
            self.assertEqual(sorted(os.listdir(tmp_dir)), ["01.html", "01.log"])
            with open(os.path.join(tmp_dir, "01.log"), encoding="utf-8") as inp:
                log_file_content = inp.read()
            self.assertTrue("x-engine" in log_file_content.lower())

    def test_log_dir_response_content_thread(self):
        with temp_dir() as tmp_dir:
            reset_request_counter()

            grab = build_grab()
            grab.setup(log_dir=tmp_dir)
            self.server.add_response(
                Response(data=b"omsk", headers=[("X-Engine", "PHP")])
            )

            self.assertEqual(os.listdir(tmp_dir), [])

            def func():
                grab.go(self.server.get_url())

            thread = threading.Thread(target=func)
            thread.start()
            thread.join()

            files = os.listdir(tmp_dir)
            self.assertEqual(2, len([x for x in files if "01-thread" in x]))
            fname = [x for x in files if x.endswith(".log")][0]
            with open(os.path.join(tmp_dir, fname), encoding="utf-8") as inp:
                log_file_content = inp.read()
            self.assertTrue("x-engine" in log_file_content.lower())

    # def test_log_dir_response_network_error(self):
    #    with temp_dir() as tmp_dir:
    #        reset_request_counter()

    #        grab = build_grab()
    #        grab.setup(log_dir=tmp_dir, timeout=1, user_agent="Perl", debug=True)
    #        self.server.add_response(
    #            Response(data=b"omsk", headers=[("X-Engine", "PHP")], sleep=2)
    #        )

    #        self.assertEqual(os.listdir(tmp_dir), [])
    #        try:
    #            grab.go(self.server.get_url())
    #        except GrabTimeoutError:
    #            pass

    #        self.assertEqual(sorted(os.listdir(tmp_dir)), ["01.html", "01.log"])
    #        with open(os.path.join(tmp_dir, "01.log"), encoding="utf-8") as inp:
    #            log_file_content = inp.read()
    #        self.assertTrue("user-agent: perl" in log_file_content.lower())

    def test_log_dir_request_content_is_empty(self):
        self.server.add_response(Response())
        with temp_dir() as tmp_dir:
            reset_request_counter()

            grab = build_grab()
            grab.setup(log_dir=tmp_dir)
            grab.setup(headers={"X-Name": "spider"}, post="xxxPost")

            self.assertEqual(os.listdir(tmp_dir), [])
            grab.go(self.server.get_url())
            self.assertEqual(sorted(os.listdir(tmp_dir)), ["01.html", "01.log"])
            with open(os.path.join(tmp_dir, "01.log"), encoding="utf-8") as inp:
                log_file_content = inp.read()
            self.assertFalse("X-Name" in log_file_content)
            self.assertFalse("xxxPost" in log_file_content)

    # because urllib3 does not collects request headers
    # def test_log_dir_request_content_headers_and_post(self):
    #    self.server.add_response(Response())
    #    with temp_dir() as tmp_dir:
    #        reset_request_counter()

    #        grab = build_grab()
    #        grab.setup(log_dir=tmp_dir, debug=True)
    #        grab.setup(headers={"X-Name": "spider"}, post={"xxx": "Post"})

    #        self.assertEqual(os.listdir(tmp_dir), [])
    #        grab.go(self.server.get_url())
    #        self.assertEqual(sorted(os.listdir(tmp_dir)), ["01.html", "01.log"])
    #        with open(os.path.join(tmp_dir, "01.log"), encoding="utf-8") as inp:
    #            log_file_content = inp.read()
    #        # if not 'x-name' in log_file_content.lower():
    #        #    print('CONTENT OF 01.log:')
    #        #    print(log_file_content)
    #        self.assertTrue("x-name" in log_file_content.lower())
    #        self.assertTrue("xxx=post" in log_file_content.lower())

    def test_debug_post(self):
        grab = build_grab(debug_post=True)
        grab.setup(post={"foo": "bar"})
        self.server.add_response(Response(data=b"x"))
        grab.go(self.server.get_url())
        self.assertEqual(b"x", grab.doc.body)

    def test_debug_nonascii_post(self):
        self.server.add_response(Response())
        grab = build_grab(debug=True)
        grab.setup(post="фыва".encode("cp1251"))
        grab.go(self.server.get_url())

    def test_debug_nonascii_multipart_post(self):
        self.server.add_response(Response())
        grab = build_grab(debug=True)
        grab.setup(charset="cp1251", multipart_post=[("x", "фыва".encode("cp1251"))])
        grab.go(self.server.get_url())

    def test_debug_post_integer_bug(self):
        grab = build_grab(debug_post=True)
        grab.setup(post={"foo": 3})
        self.server.add_response(Response(data=b"x"))
        grab.go(self.server.get_url())
        self.assertEqual(b"x", grab.doc.body)

    def test_debug_post_big_str(self):
        self.server.add_response(Response())
        grab = build_grab(debug_post=True)
        big_value = "x" * 1000
        grab.setup(post=big_value)
        grab.go(self.server.get_url())
        self.assertEqual(self.server.get_request().data, big_value.encode())

    def test_debug_post_dict_big_value(self):
        self.server.add_response(Response())
        grab = build_grab(debug_post=True)
        big_value = "x" * 1000
        grab.setup(
            post={
                "foo": big_value,
            }
        )
        grab.go(self.server.get_url())
        self.assertEqual(
            self.server.get_request().data, ("foo=%s" % big_value).encode()
        )

    def test_log_request_extra_argument(self):
        self.server.add_response(Response())
        grab = build_grab()
        grab.go(self.server.get_url())
        with patch.object(base.logger_network, "debug") as mocked:
            grab.log_request()
            args = mocked.mock_calls[0][1]
            self.assertEqual("", args[3])

        with patch.object(base.logger_network, "debug") as mocked:
            grab.log_request(extra="zz")
            args = mocked.mock_calls[0][1]
            self.assertEqual("[zz] ", args[3])

    def test_setup_document_logging(self):
        grab = Grab()
        grab.setup_document(b"abc")
        with patch.object(base.logger_network, "debug") as mocked:
            grab.log_request()
            args = mocked.mock_calls[0][1]
            # request_counter is None and formatted as "NA"
            self.assertEqual("NA", args[1])

    #    grab.log_request()  # should not raise exception
