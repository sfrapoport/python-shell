import unittest, sys, shell, cStringIO, tempfile
        
class testOneRedirect(unittest.TestCase):
    #Using named files helps modulate this!
    def test_write_to_hello(self):
        with tempfile.NamedTemporaryFile() as f:
            shell.run_all_commands([['echo', 'hello', '>', f.name]])
            f.seek(0)
            self.assertEqual(f.read(), 'hello\n')
    @unittest.skip('this does not work yet')
    def test_read_from_hello(self):
        with tempfile.NamedTemporaryFile() as f:
            with tempfile.TemporaryFile() as o:
                f.write('hello')
                shell.run_all_commands([['cat', '<', f.name]], o.fileno())
                import time
                time.sleep(1)
                o.seek(0)
                self.assertEqual(o.read(), 'hello\n')

class testOneCommand(unittest.TestCase):
    def test_echo_hello_hello(self):
        with tempfile.TemporaryFile() as f:
            shell.run_all_commands([['echo', 'hello', 'hello']],
                    f.fileno())
            f.seek(0)
            self.assertEqual(f.read(), 'hello hello\n')

class testOnePipe(unittest.TestCase):
    def test_pipe_transform(self):
        with tempfile.TemporaryFile() as f:
            shell.run_all_commands([['echo', 'hello', 'hello'], ['tr', 'h', 'y']],
                    f.fileno())
            f.seek(0)
            self.assertEqual(f.read(), 'yello yello\n')

    def test_ls_head(self):
        with tempfile.TemporaryFile() as f:
            shell.run_all_commands([['ls'], ['head']],
                    f.fileno())
            f.seek(0)
            self.assertEqual(len(f.read().split('\n')), 11)

class testTwoPipes(unittest.TestCase):
    def test_ls_head_head(self):
        with tempfile.TemporaryFile() as f:
            shell.run_all_commands([['ls'], ['head'], ['head']],
                    f.fileno())
            f.seek(0)
            self.assertEqual(len(f.read().split('\n')), 11)

    def test_ls_head_tr(self):
        with tempfile.TemporaryFile() as f:
            shell.run_all_commands([['ls'], ['head'], ['tr', 's', 's']],
                    f.fileno())
            f.seek(0)
            self.assertEqual(len(f.read().split('\n')), 11)

class testPipeRedirect(unittest.TestCase):
    def test_ls_head_write(self):
        with tempfile.NamedTemporaryFile() as o:
            shell.run_all_commands([['ls'], ['head', '>', o.name]])
            o.seek(0)
            self.assertEqual(len(o.read().split('\n')), 11)
            
unittest.main()
