# Test the signal module
from test.test_support import verbose, TestSkipped, TestFailed
import signal
import os, sys, time

if sys.platform[:3] in ('win', 'os2') or sys.platform=='riscos':
    raise TestSkipped, "Can't test signal on %s" % sys.platform

if verbose:
    x = '-x'
else:
    x = '+x'
pid = os.getpid()

# Shell script that will send us asynchronous signals
script = """
 (
        set %(x)s
        sleep 2
        kill -HUP %(pid)d
        sleep 2
        kill -USR1 %(pid)d
        sleep 2
        kill -USR2 %(pid)d
 ) &
""" % vars()

def handlerA(*args):
    if verbose:
        print "handlerA", args

class HandlerBCalled(Exception):
    pass

def handlerB(*args):
    if verbose:
        print "handlerB", args
    raise HandlerBCalled, args

signal.alarm(20)                        # Entire test lasts at most 20 sec.
hup = signal.signal(signal.SIGHUP, handlerA)
usr1 = signal.signal(signal.SIGUSR1, handlerB)
usr2 = signal.signal(signal.SIGUSR2, signal.SIG_IGN)
alrm = signal.signal(signal.SIGALRM, signal.default_int_handler)

try:
    os.system(script)

    print "starting pause() loop..."

    try:
        while 1:
            if verbose:
                print "call pause()..."
            try:
                signal.pause()
                if verbose:
                    print "pause() returned"
            except HandlerBCalled:
                if verbose:
                    print "HandlerBCalled exception caught"
                else:
                    pass

    except KeyboardInterrupt:
        if verbose:
            print "KeyboardInterrupt (assume the alarm() went off)"

finally:
    signal.signal(signal.SIGHUP, hup)
    signal.signal(signal.SIGUSR1, usr1)
    signal.signal(signal.SIGUSR2, usr2)
    signal.signal(signal.SIGALRM, alrm)

class WakeupSignalTests(unittest.TestCase):
    TIMEOUT_FULL = 10
    TIMEOUT_HALF = 5

    def test_wakeup_fd_early(self):
        import select

        signal.alarm(1)
        before_time = time.time()
        # We attempt to get a signal during the sleep,
        # before select is called
        time.sleep(self.TIMEOUT_FULL)
        mid_time = time.time()
        self.assert_(mid_time - before_time < self.TIMEOUT_HALF)
        select.select([self.read], [], [], self.TIMEOUT_FULL)
        after_time = time.time()
        self.assert_(after_time - mid_time < self.TIMEOUT_HALF)

    def test_wakeup_fd_during(self):
        import select

        signal.alarm(1)
        before_time = time.time()
        # We attempt to get a signal during the select call
        self.assertRaises(select.error, select.select,
            [self.read], [], [], self.TIMEOUT_FULL)
        after_time = time.time()
        self.assert_(after_time - before_time < self.TIMEOUT_HALF)

    def setUp(self):
        import fcntl

        self.alrm = signal.signal(signal.SIGALRM, lambda x,y:None)
        self.read, self.write = os.pipe()
        flags = fcntl.fcntl(self.write, fcntl.F_GETFL, 0)
        flags = flags | os.O_NONBLOCK
        fcntl.fcntl(self.write, fcntl.F_SETFL, flags)
        self.old_wakeup = signal.set_wakeup_fd(self.write)

    def tearDown(self):
        signal.set_wakeup_fd(self.old_wakeup)
        os.close(self.read)
        os.close(self.write)
        signal.signal(signal.SIGALRM, self.alrm)


def test_main():
    if sys.platform[:3] in ('win', 'os2') or sys.platform == 'riscos':
        raise test_support.TestSkipped("Can't test signal on %s" % \
                                       sys.platform)

    test_support.run_unittest(WakeupSignalTests)


if __name__ == "__main__":
    test_main()
