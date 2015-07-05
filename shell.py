import signal
import sys
import os

def read_in():
    sys.stdout.write('YO! >')
    content = sys.stdin.readline()[:-1]
    return content

# First write for one command & one file to write to

def write_handler(read_fd, args): 
    commands = []
    operations = []
    for arg in args:
        if arg == '>':
            commands.append(operations)
            operations = []
        else:
            operations.append(arg)
    commands.append(operations)
    waits = len(commands)
    write_to = os.open(commands[1][0], os.O_WRONLY|os.O_CREAT|os.O_TRUNC)
    command = commands[0]
    write_from(command, read_fd, write_to)

def pipe_handler(args):
    # is there a way to do this more pythonically?
    commands = []
    operations = []
    for arg in args:
        if arg == '|':
            commands.append(operations)
            operations = []
        else:
            operations.append(arg)
    commands.append(operations)
    waits = len(commands)
    stdin_out = ( 0, 1 )
    while len(commands) > 1:
        if not 'next_pipe' in locals():
            current_pipe = stdin_out
        else: 
            current_pipe = next_pipe
            print 'current pipe: ', current_pipe
        next_pipe = os.pipe()
        command = commands[0]
        commands = commands[1:]
        write_from(command, current_pipe, next_pipe) 
    command = commands[0]
    if current_pipe != (0, 1): 
        os.close(current_pipe[0])
        os.close(current_pipe[1])
    if '>' in command:
        os.close(next_pipe[1])
        write_handler(next_pipe[0], command)
    else: 
        write_from(command, next_pipe, stdin_out)
    if next_pipe != (0, 1): 
        os.close(next_pipe[1])
        os.close(next_pipe[0])
    print 'waiting for: ', waits, ' child processes'
    for i in xrange(waits):
        os.wait()

def write_from(command, read_fd_or_pipe, write_fd_or_pipe):
    if isinstance(read_fd_or_pipe, (list, tuple)):
        read_fd = read_fd_or_pipe[0]
    else:
        read_fd = read_fd_or_pipe
    if isinstance(write_fd_or_pipe, (list, tuple)):
        write_fd = write_fd_or_pipe[1]
    else: 
        write_fd = write_fd_or_pipe
    write_process = os.fork()
    if write_process == 0:
        exec_args = (command[0], command)
        print 'file descriptors: ', read_fd, write_fd
        os.dup2(write_fd, 1)
        os.dup2(read_fd, 0)
        if isinstance(read_fd_or_pipe, (list, tuple)) and read_fd_or_pipe != (0, 1):
            os.close(read_fd_or_pipe[0])
            os.close(read_fd_or_pipe[1])
        elif read_fd != 0: 
            os.close(read_fd)
        if isinstance(write_fd_or_pipe, (list, tuple)) and write_fd_or_pipe != (0, 1):
            os.close(write_fd_or_pipe[0])
            os.close(write_fd_or_pipe[1])
        elif write_fd != 1: 
            os.close(write_fd)
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
        os.execvp(*exec_args)

def main():
    while True:    
        line = read_in()
        if line == 'quit':
            return False
        args = line.split(' ')
        cmd = args[0]
        # To generalize, have to enable pipe to cooperate with other 
        # file redirection (this might require returning to main)
        if len(args) > 1 and '|' in args:
            pipe_handler(args)
        elif len(args) > 1 and '>' in args:
            write_handler(0, args)
            os.wait()
        elif cmd == 'cd':
            os.chdir(os.path.abspath(args[1]))
        else:
            newpid = os.fork() 
            if newpid == 0:
                os.execvp(args[0], args)
            os.wait()

if __name__=='__main__':
    main()

