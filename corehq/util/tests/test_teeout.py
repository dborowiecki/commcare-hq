import re
import sys
from contextlib import contextmanager
from io import StringIO

from django.test import SimpleTestCase

from corehq.util.teeout import tee_output
from testil import assert_raises, replattr, eq


# Workaround for https://api.travis-ci.org/v3/job/545327504/log.txt
class TestTee(SimpleTestCase):

    def test_tee_output(self):
        fileobj = StringIO()
        with assert_raises(Error), stdfake() as fake, tee_output(fileobj):
            print("testing...")
            sys.stderr.write("fail.\n")
            raise Error("stop")
        eq(fake.stdout.getvalue(), "testing...\n")
        eq(fake.stderr.getvalue(), "fail.\n")
        eq(sanitize_tb(fileobj.getvalue()),
            "testing...\n"
            "fail.\n"
            "Traceback (most recent call last):\n"
            "  ...\n" +
            "corehq.util.tests.test_teeout.Error: stop\n")


def test_tee_output_with_KeyboardInterrupt():
    fileobj = StringIO()
    with assert_raises(KeyboardInterrupt), stdfake() as fake, tee_output(fileobj):
        raise KeyboardInterrupt("errrt")
    eq(fake.stdout.getvalue(), "")
    eq(fake.stderr.getvalue(), "")
    eq(sanitize_tb(fileobj.getvalue()),
        "Traceback (most recent call last):\n"
        "  ...\n"
        "KeyboardInterrupt: errrt\n")


def test_tee_output_with_SystemExit():
    fileobj = StringIO()
    with assert_raises(SystemExit), stdfake() as fake, tee_output(fileobj):
        raise SystemExit(1)
    eq(fake.stdout.getvalue(), "")
    eq(fake.stderr.getvalue(), "")
    eq(fileobj.getvalue(), "")


@contextmanager
def stdfake():
    class fake(object):
        stdout = StringIO()
        stderr = StringIO()
    with replattr((sys, "stdout", fake.stdout), (sys, "stderr", fake.stderr)):
        yield fake


def sanitize_tb(value):
    return re.sub(
        r"(Traceback .*:\n)(?:  .*\n)+",
        r"\1  ...\n",
        value,
        flags=re.MULTILINE,
    )


class Error(Exception):
    pass
