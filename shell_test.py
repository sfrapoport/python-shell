import unittest, sys, shell, cStringIO, tempfile

class testEcho(unittest.TestCase):
    def test_echo_hello_hello(self):
        with tempfile.TemporaryFile() as f:
            shell.run_all_commands([['echo', 'hello', 'hello']],
                    f.fileno())
            import time
            f.seek(0)
            self.assertEqual(f.read(), 'hello hello\n')
    #def test_pipe_transform(self):
    #    with tempfile.TemporaryFile() as f:
    #        shell.run_all_commands([['echo', 'hello', 'hello'], ['tr', 'h', 'y']],
    #                f.fileno())
    #        f.seek(0)
    #        self.assertEqual(f.read(), 'yello yello\n')

    def test_ls_head(self):
        with tempfile.TemporaryFile() as f:
            shell.run_all_commands([['ls'], ['head']],
                    f.fileno())
            import time
            f.seek(0)
            self.assertEqual(len(f.read().split('\n')), 11)
unittest.main()
