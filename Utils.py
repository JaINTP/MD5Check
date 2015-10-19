import ctypes
import inspect
from platform import system

__version__ = '0.1'
__author__ = 'JaINTP - Jai Brown'
__maintainer__ = 'JaINTP - Jai Brown'
__status__ = 'Development'

banner = """
%b'||    ||' '||''|.   ____    ..|'''.| '||                      '||      .
%b |||  |||   ||   ||  ||  ` .|'     '   || ..     ....    ....   ||  ..
%b |'|..'||   ||    || ||_   ||          ||' ||  .|...|| .|   ''  || .'
%b | '|' ||   ||    || |/ \  '|.      .  ||  ||  ||      ||       ||'|.
%b.|. | .||. .||...|'     ))  ''|....'  .||. ||.  '|...'  '|...' .||. ||.
                       //
                      /'

%b... ...  .... ...
%b ||'  ||  '|.  |
%b ||    |   '|.|
%b ||...'     '|
%b ||      .. |
%b''''      ''
"""


class _ConsoleColourer(object):
    """Basic class to handle the colouring of console output. Only
    supports ANSI escape sequences.

    @note: Currently no Windows support.
    @todo: Add Windows support.
    """

    __slots__ = ['__colours',]

    def __init__(self):
        """Initialises colour codes for formatting use."""
        super(_ConsoleColourer, self).__init__()
        self.__colours = {
            'w': 0,   # White
            'r': 31,  # Red
            'g': 32,  # Green
            'o': 33,  # Orange
            'b': 34,  # Blue
            'p': 35,  # Purple
            'c': 36,  # Cyan
            'G': 37,  # Grey
        }

    def _format(self, string):
        """Formats a given string.

        @type string: string
        @param string: String to be formatted and printed.

        @rtype: string
        @return: The resulting formatted string.
        """
        base = '\033[{0}m'

        for char in self.__colours:
            if system() is 'Windows':
                string = string.replace('%' + char, '')
            else:
                string = string.replace('%' + char,
                                        base.format(self.__colours[char]))
                string = '{}\033[0m'.format(string)

        return string

    def print(self, string):
        """Outputs a given string in colour.

        @type string: string
        @param string: String to be formatted and printed.
        """
        print(self._format(string))

    def input(self, string):
        """Outputs a given string in colour and waits for input.

        @type string: string
        @param string: String to be formatted and printed.

        @rtype: string
        @return: The user's input string.
        """
        return input(self._format(string))

CC = _ConsoleColourer()


# Following code found here: http://stackoverflow.com/a/6357799
def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid,
                                                     ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)
