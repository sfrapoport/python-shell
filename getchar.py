import os
import sys
import tty, termios
# from curtsies import Input

def get_up_or_down():
    buffer = ''
    c = read_char_raw()
    if c=='up':
        return 'up'
    elif c=='down':
        return 'down'
    elif c=='enter':
        return 'enter'
    else:
        buffer += c
        sys.stdout.write(buffer)
        return buffer

# Read one raw character at a time!!!
def read_char_raw():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    new = termios.tcgetattr(fd)
    new[3] = new[3] | termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, new)
    try:
        tty.setraw(fd)
        c = sys.stdin.read(1)
        if c == '\x1b': # match escape prefix for up key
            n = sys.stdin.read(2) # escape is 3 bytes
            if n == '[A': # UP ARROW
                return 'up'
            elif n == '[B':
                return 'down'
            else:
                return ''
        elif c=='\r':
            return 'enter'
        else:
            return c
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)



