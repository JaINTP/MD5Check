#! /usr/bin/env python3

from abc import ABCMeta, abstractmethod
import argparse
from hashlib import md5
import json
from os.path import isfile
from string import ascii_letters
from threading import Thread
from time import sleep
from urllib.request import Request
from urllib.error import URLError
from urllib.request import urlopen

# Personal imports
import Utils

__version__ = '0.1'
__author__ = 'JaINTP - Jai Brown'
__maintainer__ = 'JaINTP - Jai Brown'
__status__ = 'Development'


class Cracker(metaclass=ABCMeta):
    """ Abstract base class for cracker implementations."""

    __slots__ = []

    @abstractmethod
    def start(self):
        """Main method for cracker classes."""
        return

    @abstractmethod
    def check_hash(self, string):
        """Checks a given hash against an online database.

        @type string:  string
        @param string: The hash to be checked.

        @rtype:  string or None
        @return: The hash's plain text if successful, else None.
        """
        return


class OnlineCracker(Cracker):
    """A class that handles discovering the plain text equivalent of an MD5
    hash via ODS (Online Database Search).
    """

    __slots__ = [
        '__delay',
        '__in_file',
        '__out_file',
        '__servers',
        '__single',
        '__total',
    ]

    def __init__(self, args):
        """Constructor.
        Initialises all variables and starts the main method.
        """
        super(OnlineCracker, self).__init__()

        self.__delay = args.delay
        self.__in_file = args.in_file
        self.__out_file = args.out_file
        self.__single = True if args.test else args.single
        self.__total = 0

        if not isfile('servers.json'):
            Utils.CC.print('%g[%o?%g] %bA servers file does not yet exist.%o')
            Utils.CC.print('%g[%o?%g] %bPlease go to %ohttp://md5crack.com/api '
                           'and retrieve an API key.')
            api_key = Utils.CC.input('%g[%o?%g] API Key%o: ')

            self.create_servers(api_key)

        self.__servers = self.load_servers()

        if args.test:
            if not args.single:
                MD5Check.stop('Single mode should also be used while running '
                              'test mode!')
            Utils.CC.print('%g[%Gi%g] %bCreating test files%G:   %o{} and {}'
                           .format(self.__in_file, self.__out_file))
            MD5Check.ready_test(self.__in_file, self.__out_file)

        self.start()

    def start(self):
        """Main method for the online crack class."""
        Utils.CC.print('\n%g  -------------------------------------------------'
                       '------------  ')
        Utils.CC.print('%g[%Gi%g] %bBeginning operation!')
        for string in MD5Check.read_file(self.__in_file):
            if not self.__single:
                string = string.split(':')
            result = self.check_hash(string)

            if result is not None:
                if self.__single:
                    string = '{}:{}'.format(string, result)
                else:
                    string = '{}:{}'.format(string[0], result)

                MD5Check.write_file(self.__out_file, string, True)
                self.__total += 1
                Utils.CC.print('%g[%Gi%g] %bHash found%G:            %o{}'
                               .format(string))

            sleep(self.__delay)

        Utils.CC.print('%g[%Gi%g] %bTotal hashes found%G:    %o{}'
                       .format(self.__total))
        Utils.CC.print('%g[%Gi%g] %bAll hashes written to%G: %o{}'
                       .format(self.__out_file))

    def check_hash(self, string):
        """Checks a given hash against an online database.

        @type string:  string
        @param string: The hash to be checked.

        @rtype:  string or None
        @return: The hash's plain text if successful, else None.
        """
        ret = None

        if not self.__single:
            string = string[1]

        for server in self.__servers:
            result = self.get_server_data(server['url']
                                          .format(server['api_key'], string))

            if result['code'] == 6:
                ret = result['phrase']
                break
            elif result['code'] == 3:
                MD5Check.stop('You have overused your query limit!')

        return ret

    def get_server_data(self, url):
        """Handles retrieving data from the server.

        @type url:  string
        @param url: The URL to retrieve json data from.

        @rtype: dict
        @return: The resulting data.
        """
        try:
            request = Request(url,
                              data=None,
                              headers={
                                  'User-Agent':
                                  'Mozilla/5.0 (Windows NT 6.1) '
                                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                                  'Chrome/41.0.2228.0 Safari/537.36'
                              })
            contents = urlopen(request).read().decode('utf-8')
            return json.loads(contents)
        except URLError as e:
            MD5Check.stop('Encountered a URLError - {}'.format(e.reason))

    def load_servers(self):
        """Loads a list of servers that host a json database from file.

        @rtype:  list
        @return: List of servers retrieved from the servers.json file.
        """
        ret = list()

        with open('servers.json', 'r') as fileObj:
            ret = json.load(fileObj)
        num = len(ret)
        Utils.CC.print('%g[%Gi%g] %b{} server{} loaded!'
                       .format(num, 's' if num > 1 else ''))

        return ret

    def create_servers(self, api_key):
        """Creates the default servers.json file using the user's API Key.

        @type api_key:  string
        @param api_key: The API Key required to use the md5crack.com API.
        """
        servers = [
            {"url": "http://api.md5crack.com/crack/{}/{}", "api_key": api_key},
        ]

        result = self.get_server_data(servers[0]['url']
                                      .format(servers[0]['api_key'],
                                              '06d80eb0c50b49a509b49f2424e8c805'
                                              ))

        if result['code'] == 4:
            MD5Check.stop('Invalid API Key! Please get a new one, and try '
                          'again.')

        with open('servers.json', 'w') as file_obj:
            json.dump(servers, file_obj)

        Utils.CC.print('%g[%Gi%g] %bDefault servers file created!')


class DictionaryCracker(Cracker):
    """A class that handles discovering the plain text equivalent of an MD5
    hash via the use of a dictionary file.
    """

    __slots__ = [
        '__dict_file',
        '__in_file',
        '__out_file',
        '__single',
        '__test',
        '__total'
    ]

    def __init__(self, args):
        """Constructor.
        Initialises all variables and starts the main method.
        """
        super(DictionaryCracker, self).__init__()

        self.__dict_file = args.dict_file
        self.__in_file = args.in_file
        self.__out_file = args.out_file
        self.__single = True if args.test else args.single
        self.__total = 0

        if args.test:
            if not args.single:
                MD5Check.stop('Single mode should also be used while running '
                              'test mode!')
            Utils.CC.print('%g[%Gi%g] %bCreating test files%G:   %o{} and {}'
                           .format(self.__in_file, self.__out_file))
            MD5Check.ready_test(self.__in_file, self.__out_file)

        self.start()

    def start(self):
        """Main method for the dictionary crack class."""
        for string in MD5Check.read_file(self.__in_file):
            if not self.__single:
                string = string.split(':')
            result = self.check_hash(string)

            if result[0]:
                if self.__single:
                    string = '{}:{}'.format(string, result[1])
                else:
                    string = '{}:{}'.format(string[0], result[1])

                MD5Check.write_file(self.__out_file, string, True)
                self.__total += 1
                Utils.CC.print('%g[%Gi%g] %bHash found%G:            %o{}'
                               .format(string))

        Utils.CC.print('%g[%Gi%g] %bTotal hashes found%G:    %o{}'
                       .format(self.__total))
        Utils.CC.print('%g[%Gi%g] %bAll hashes written to%G: %o{}'
                       .format(self.__out_file))

    def check_hash(self, original_hash):
        """Checks whether the MD5 equivelant of a string read from a file
        matches original_hash.

        @type original_hash:  string.
        @param original_hash: The hash to be found.

        @rtype:  list
        @return: List containing a bool representation of whether the original
                 hash matches the hash represented by param string, and the
                 original plain text string.
        """
        plain_string = ''
        new_hash = ''

        for plain_string in MD5Check.read_file(self.__dict_file):
            new_hash = md5(plain_string.encode()).hexdigest()

            if new_hash == original_hash:
                break

        return [new_hash == original_hash, plain_string]


class BruteforceCracker(Cracker):
    """A class that handles discovering the plain text equivalent of an MD5
    hash via bruteforce recursive string generation.
    """

    __slots__ = [
        '__in_file',
        '__max_length',
        '__out_file',
        '__result',
        '__single',
        '__test',
        '__total',
        '__total_strings',
    ]

    def __init__(self, args):
        """Constructor.
        Initialises all variables and starts the main method.
        """
        super(BruteforceCracker, self).__init__()
        self.__in_file = args.in_file
        self.__max_length = args.length
        self.__out_file = args.out_file
        self.__result = None
        self.__single = args.single
        self.__test = args.test
        self.__total = 0
        self.__total_strings = 0

        self.start()

    def start(self):
        """Main method for the bruteforce crack class."""
        for string in MD5Check.read_file(self.__in_file):
            if not self.__single:
                string = string.split(':')

            self.__result = None
            brute_thread = Thread(target=self._run)
            brute_thread._args = (string, brute_thread)
            brute_thread.start()
            brute_thread.join()

            if self.__result:

                if self.__single:
                    string = '{}:{}'.format(string, self.__result)
                else:
                    string = '{}:{}'.format(string[0], self.__result)

                MD5Check.write_file(self.__out_file, string, True)
                self.__total += 1
                Utils.CC.print('%g[%Gi%g] %bHash found%G:            %o{}'
                               .format(string))

        Utils.CC.print('%g[%Gi%g] %bTotal hashes found%G:    %o{}'
                       .format(self.__total))
        Utils.CC.print('%g[%Gi%g] %bAll hashes written to%G: %o{}'
                       .format(self.__out_file))

    def _run(self, hash, thread_obj):
        """Thread's run method.
        Initialises the recursive string generator.
        """
        for width in range(1, self.__max_length + 1):
            self._recurse(width, 0, '', hash, thread_obj)
            if self.__result is not None:
                break

    def check_hash(self, string, original_hash):
        """Checks a given string's MD5 equivilant against an existing hash.

        @type string:  string
        @param string: The hash to be checked.

        @rtype:  bool
        @return: Whether the two MD5 hashes match one another.
        """
        return original_hash == md5(string.encode()).hexdigest()

    def _recurse(self, width, position, string, original_hash, thread_obj):
        """ Recursively calls itself to generate strings.

        @type width:  int
        @param width: Length of current string.

        @type position:  int
        @param position: Current string position to modify.

        @type string: string
        @param string: The current generated string.

        @type original_hash:  string
        @param original_hash: The original hash for comparison operations.

        @type thread_obj:  threading.Thread
        @param thread_obj: This thread. Used for termination.
        """
        temp = ''
        for letter in ascii_letters:
            temp = '{}{}'.format(string, letter)
            if position < width - 1:
                self._recurse(width,
                              position + 1,
                              temp,
                              original_hash, thread_obj)
            if self.check_hash(temp, original_hash):
                self.__result = temp
                Utils.stop_thread(thread_obj)


class MD5Check(object):
    """The main application class."""

    def __init__(self, cli_args):
        """Constructor.
        Initialises all variables and begins the application.
        """
        Utils.CC.print(Utils.banner)
        if cli_args.command == 'online':
            OnlineCracker(cli_args)
        elif cli_args.command == 'dictionary':
            DictionaryCracker(cli_args)
        elif cli_args.command == 'bruteforce':
            BruteforceCracker(cli_args)

    @staticmethod
    def ready_test(in_file, out_file):
        """Creates default input and output files for a test run of the
        application.

        @type in_file: string
        @param in_file: Fully qualified path to the input file.

        @type out_file: string
        @param out_file: Fully qualified path to the output file.
        """
        with open(out_file, 'w') as fd:
            fd.write('')
        with open(in_file, 'w') as fd:
            for animal in ('dog', 'cat', 'bird', 'fish', 'bear', 'shark'):
                fd.write(md5(animal.encode()).hexdigest() + '\n')

    @staticmethod
    def read_file(filename):
        """Reads a list of hashes from the specified input file.

        @type filename:  string
        @param filename: Fully qualified path to the file to be read.

        @rtype:  list
        @return: The contents of the file in list form.
        """
        ret = list()

        try:
            with open(filename, 'r') as fileObj:
                ret = [line.strip() for line in fileObj.readlines()]
        except IOError:
            MD5Check.stop('%oFile %G{} %ocannot be read from!'
                          .format(filename))

        return ret

    @staticmethod
    def write_file(filename, data, append=False):
        """

        @type filename:  string
        @param filename: Fully qualified path for the file to be written.

        @type data:  string
        @param data: Contents of the file to be written.

        @type append:  bool
        @param append: Whether or not to open the file for writing or to append.
        """
        try:
            with open(filename, 'a' if append else 'w') as fileObj:
                fileObj.write(data + '\n')
        except IOError:
            MD5Check.stop('%oFile %G{} %ocannot be written to!'
                          .format(filename))

    @staticmethod
    def stop(error_string):
        """Outputs an error and exits the application.

        @type error_string:  string
        @param error_string: The error string to be printed.
        """
        Utils.CC.print('%g[%Gi%g] %oError%G: %o{}'.format(error_string))
        Utils.CC.print('%g[%Gi%g] %oClosing!')
        exit(1)


if __name__ == '__main__':
    # Create argument parser.
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    # Positional arguments.
    parser.add_argument('in_file',
                        type=str,
                        help='File from which the hashes should be read.')
    parser.add_argument('out_file',
                        type=str,
                        help='File to which the hashes should be written.')

    # Optional arguments.
    parser.add_argument('-t',
                        '--test',
                        action='store_true',
                        help='Run a test case generating basic hashes. '
                             'Single mode should also be used while running '
                             'test mode!')
    parser.add_argument('-s',
                        '--single',
                        action='store_true',
                        help='With this parameter, each line should consist of '
                             'a lone MD5 hash!')

    # Subparsers.
    online_parser = subparsers.add_parser('online')
    dictionary_parser = subparsers.add_parser('dictionary')
    bruteforce_parser = subparsers.add_parser('bruteforce')

    online_parser.add_argument('-d',
                               '--delay',
                               type=int,
                               default=4,
                               help='Delay in seconds between each hash check.')
    dictionary_parser.add_argument('dict_file',
                                   type=str,
                                   help='Dictionary file containing plain text '
                                        'words.')
    bruteforce_parser.add_argument('-l',
                                   '--length',
                                   type=int,
                                   default=12,
                                   help='Maximum length of generated strings. '
                                        'Default is 12.')

    args = parser.parse_args()

    MD5Check(args)
