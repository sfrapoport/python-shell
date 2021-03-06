import signal, sys, os
import history
from blessed import Terminal

STDIN_OUT = ( 0, 1 )
FDS_TO_CLOSE = []

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
    write_process = os.fork()
    if write_process == 0:
        exec_args = (command[0], command)
        os.dup2(read_fd, 0)
        os.dup2(write_fd, 1)
        close_fds(fds_to_close)
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
        os.execvp(*exec_args)
        
def close_fds(fds):
    for fd in fds:
        if fd not in STDIN_OUT:
            os.close(fd)

# CHANGE NAME: should just be redirect_from_file
def redirect_from_file(commands, write_to):
    global FDS_TO_CLOSE
    file_name = [elem[1] for elem in zip(commands, commands[1:])
            if elem[0] == '<']
    read_file = os.open(file_name[0], os.O_RDONLY)
    pre_redirect_args = [cmd for index, cmd in enumerate(commands) 
            if index < commands.index('<')]
    FDS_TO_CLOSE += [read_file]
    write_from(pre_redirect_args, read_file, write_to[1], write_to + (read_file,))
# CHANGE NAME: should just be redirect_to_file
def redirect_to_file(commands, read_from): 
    global FDS_TO_CLOSE
    file_name = [elem[1] for elem in zip(commands, commands[1:])
            if elem[0] == '>']
    write_file = os.open(file_name[0], os.O_WRONLY|os.O_CREAT|os.O_TRUNC)
    pre_redirect_args = [cmd for index, cmd in enumerate(commands) 
            if index < commands.index('>')]
    FDS_TO_CLOSE += [write_file]
    write_from(pre_redirect_args, read_from[0], write_file, read_from + (write_file,))

def run_all_commands(commands, write_fd=1):
    global FDS_TO_CLOSE
    FDS_TO_CLOSE = []
    
    num_child_processes = len(commands)
    # CASE: AT LEAST ONE PIPE...
    while len(commands) > 1:
        first_command = commands[0]
        commands = commands[1:]
        # CASE: FIRST command - get input to launch processes
        if not 'next_pipe' in locals():
            if '<' in first_command:
                ++num_child_processes
                redirect_from_file(first_command, STDIN_OUT)
            current_pipe = STDIN_OUT
        else: 
            FDS_TO_CLOSE += current_pipe
            current_pipe = next_pipe
        next_pipe = os.pipe()
        # Route read/write to file commands to handlers
        write_from(first_command, current_pipe[0], next_pipe[1], current_pipe + next_pipe) 

    last_command = commands[0]

    # CASE: NO PIPES
    if 'next_pipe' not in locals():
        if '<' in last_command:
            redirect_from_file(last_command, STDIN_OUT)
            os.wait()
        elif '>' in last_command:
            redirect_to_file(last_command, STDIN_OUT)
            os.wait()
        elif last_command[0] == 'cd':
            os.chdir(os.path.abspath(last_command[1]))
        else:
            newpid = os.fork() 
            if newpid == 0:
                if write_fd != 1:
                    os.dup2(write_fd, 1)
                    os.close(write_fd)
                os.execvp(last_command[0], last_command)
            os.wait()

    # CASE: LAST COMMAND AFTER PIPES    
    else:
        FDS_TO_CLOSE += current_pipe
        if '>' in last_command:
            ++num_child_processes
            redirect_to_file(last_command, next_pipe)
        else: 
            write_from(last_command, next_pipe[0], write_fd, next_pipe)
        FDS_TO_CLOSE += next_pipe
        close_fds([fd for ind, fd in enumerate(FDS_TO_CLOSE)
            if FDS_TO_CLOSE.index(fd) == ind])
        for i in xrange(num_child_processes):
            os.wait()

def main():
    term = Terminal()
    term.stream.write('YO >')
    term.stream.flush()
    termHistory = history.CommandHistory()
    buffer = ''
    while True:    
        try: 
            with term.cbreak():
                char = term.inkey()
                if char.is_sequence:
                    if char.name == 'KEY_UP':
                        termHistory.increment_index()
                        buffer = termHistory.get_item()
                        term.stream.write(term.clear_bol)
                        term.stream.write(term.move_x(0))
                        term.stream.write('YO >')
                        term.stream.write(buffer)
                    elif char.name == 'KEY_DOWN':
                        termHistory.decrement_index()
                        buffer = termHistory.get_item()
                        term.stream.write(term.clear_bol)
                        term.stream.write(term.move_x(0))
                        term.stream.write(term.clear_bol + 'YO >')
                        term.stream.write(buffer)
                    elif char.name == 'KEY_DELETE':
                        buffer = buffer[ :-1 ]
                        term.stream.write(term.move_left)
                        term.stream.write(' ')
                        term.stream.write(term.move_left)
                    elif char.name == 'KEY_ENTER':
                        termHistory.add(buffer)
                        args = buffer.split(' ')
                        commands = separate_by_pipe(args)
                        term.stream.write('\n')
                        run_all_commands(commands, 1)
                        buffer = ''
                        term.stream.write('YO >')
        finally:
            if not char.is_sequence:
                buffer += char
                term.stream.write(char)
            term.stream.flush()

if __name__=='__main__':
    main()

