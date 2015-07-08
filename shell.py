import signal, sys, os

STDIN_OUT = ( 0, 1 )
FDS_TO_CLOSE = []

def read_in():
    sys.stdout.write('YO! >')
    content = sys.stdin.readline()[:-1]
    return content

def separate_by_pipe(args):
    commands = []
    operations = []
    for arg in args:
        if arg == '|':
            commands.append(operations)
            operations = []
        else:
            operations.append(arg)
    commands.append(operations)
    return commands

def write_from(command, read_fd, write_fd, fds_to_close):
    # print 'in write_from, running command: ', command
    write_process = os.fork()
    if write_process == 0:
        # print 'WHY AM I NOT GETTING INTO THE CHILD PROCESS?!?!?!'
        exec_args = (command[0], command)
        os.dup2(read_fd, 0)
        os.dup2(write_fd, 1)
        #CLOSE ALL FDs before EXEC
        #print 'closing fds before child process runs: ', fds_to_close
        close_fds(fds_to_close)
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
        os.execvp(*exec_args)
        
def close_fds(fds):
    for fd in fds:
        if fd not in STDIN_OUT:
            # print 'closing fd: ', fd
            os.close(fd)

# CHANGE NAME: should just be redirect_from_file
def redirect_file_to_stdin(commands, write_to):
    global FDS_TO_CLOSE
    file_name = [elem[1] for elem in zip(commands, commands[1:])
            if elem[0] == '<']
    read_file = os.open(file_name[0], os.O_RDONLY)
    print 'reading from file', read_file
    pre_redirect_args = [cmd for index, cmd in enumerate(commands) 
            if index < commands.index('<')]
    print 'command ', pre_redirect_args
    FDS_TO_CLOSE += [read_file]
    write_from(pre_redirect_args, read_file, write_to[1], write_to + (read_file,))
# CHANGE NAME: should just be redirect_to_file
def redirect_stdout_to_file(commands, read_from): 
    global FDS_TO_CLOSE
    file_name = [elem[1] for elem in zip(commands, commands[1:])
            if elem[0] == '>']
    write_file = os.open(file_name[0], os.O_WRONLY|os.O_CREAT|os.O_TRUNC)
    print 'writing to file', write_file
    pre_redirect_args = [cmd for index, cmd in enumerate(commands) 
            if index < commands.index('>')]
    FDS_TO_CLOSE += [write_file]
    print 'command ', pre_redirect_args
    write_from(pre_redirect_args, read_from[0], write_file, read_from + (write_file,))

def run_all_commands(commands, write_fd=1):
    global FDS_TO_CLOSE
    FDS_TO_CLOSE = []
    print 'newest version'
    
    num_child_processes = len(commands)
    # CASE: AT LEAST ONE PIPE...
    while len(commands) > 1:
        first_command = commands[0]
        commands = commands[1:]
        # CASE: FIRST command - get input to launch processes
        if not 'next_pipe' in locals():
            if '<' in first_command:
                ++num_child_processes
                redirect_file_to_stdin(first_command, STDIN_OUT)
            current_pipe = STDIN_OUT
        else: 
            FDS_TO_CLOSE += current_pipe
            current_pipe = next_pipe
        next_pipe = os.pipe()
        # Route read/write to file commands to handlers
        print 'writing from ', current_pipe[0], ' to ', next_pipe[1]
        write_from(first_command, current_pipe[0], next_pipe[1], current_pipe + next_pipe) 

    last_command = commands[0]

    # CASE: NO PIPES
    if 'next_pipe' not in locals():
        print 'only ONE command: ', last_command
        if '<' in last_command:
            redirect_file_to_stdin(last_command, STDIN_OUT)
            os.wait()
        elif '>' in last_command:
            redirect_stdout_to_file(last_command, STDIN_OUT)
            os.wait()
        elif last_command[0] == 'cd':
            print 'in cd handler'
            os.chdir(os.path.abspath(last_command[1]))
        else:
            print 'in regular old process'
            print last_command
            newpid = os.fork() 
            if newpid == 0:
                if write_fd != 1:
                    os.dup2(write_fd, 1)
                    os.close(write_fd)
                os.execvp(last_command[0], last_command)
            os.wait()

    # CASE: LAST COMMAND AFTER PIPES    
    # REFACTOR: os.close handling, write_from behavior
    else:
        FDS_TO_CLOSE += current_pipe
        print 'last command running', last_command
        if '>' in last_command:
            ++num_child_processes
            redirect_stdout_to_file(last_command, next_pipe)
        else: 
            print 'writing to stdout from: ', next_pipe[0]
            write_from(last_command, next_pipe[0], write_fd, next_pipe)
        FDS_TO_CLOSE += next_pipe
        close_fds([fd for ind, fd in enumerate(FDS_TO_CLOSE)
            if FDS_TO_CLOSE.index(fd) == ind])
        for i in xrange(num_child_processes):
            os.wait()


def main():
    while True:    
        line = read_in()
        if line == 'quit':
            return False
        args = line.split(' ')
        commands = separate_by_pipe(args)
        run_all_commands(commands, 1)

if __name__=='__main__':
    main()

