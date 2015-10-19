# MD5Check
Basic MD5 cracking application.
Supports dictionary, bruteforce and ODS(Online Database Search) methods.

# Important!
If you don't have one already, grab a free API Key from http://md5crack.com/api
and have it ready for the first run of the online cracker method of the application.

# Usage
Using the --help parameter should be easy enough to understand.
Basic bruteforce test.
MD5Check.py -t -s bruteforce -l 5 in.txt out.txt

Basic online test:
MD5Check.py -t -s online in.txt out.txt

Basic dictionary test:
MD5Check.py -t -s dictionary dictionary.txt in.txt out.txt