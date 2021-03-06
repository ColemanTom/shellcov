import os
import re
import subprocess  # nosec
import sys
from itertools import groupby
from pathlib import Path
from operator import itemgetter
from re import DOTALL, MULTILINE, VERBOSE

DEFAULT_PS4 = '+PS4 + ${BASH_SOURCE} + ${SECONDS}S + L${LINENO} + '
FILLER = '@@filler@@'
BASE_CMD = ['/bin/sh', '-x']
COLUMN_HEADINGS = ['Name', 'Stmts', 'Miss', 'Cover', 'Missing']

# All regex below assume that all lines in the search string have been trimmed
RE_COMMENT = re.compile(r'''^#.*|(?<!["'\\{$])#.*''', MULTILINE)
RE_ESCAPED_QUOTE = re.compile(r'''\\['"]''')
# Two line continuation adjustments. One removes it because its blank
# afterwards. The second is used to add a filler to the first line as a command
# is being executed.
RE_LINE_CONTINUATION_REMOVE = re.compile(r'^(?:\s*\\\s*?)+(?=[#\r\n\f])',
                                         MULTILINE)
RE_LINE_CONTINUATION = re.compile(r'''
    ^(?:.*?            # everything in the line leading up to
    [^\S\r\n]*[^\\]\\  # a line with a non-escaped \
    (?:[ \t]*\#\S*)?   # optionally followed by a comment
    [^\S\r\n]*\n)+     # and something on the next line
    \S*                # and finally the last lines contents
    ''', VERBOSE | MULTILINE)
RE_HEREDOC = re.compile(r'''
    (               # Have one major group so findall gets what we want
    <<-?[ \t]*(')?  # <<-' (with or without the ', spaces, -)
    ((?:[^'])+)     # the EOF type string
    \2?$            # close EOF with ' if that exists
    .*?^\s*         # Contents
    \3              # Closing capture string
    \s*$            # maybe some extra spaces
    )''', DOTALL | MULTILINE | VERBOSE)
RE_LOGIC_OPERATOR = re.compile(r'''
    ^(?:
    [{}]|             # opening/closing block
    ;|                # semi-colon only line
    then|             # opening if block
    fi|               # closing if block
    do|               # opening loop
    done|             # closing loop
    in|               # opening case statement
    esac|             # closing case statement
    [^(\r\n\f]*\)     # option in case statement
    )[ \t;]*?$
    ''', MULTILINE | VERBOSE)
RE_MULTI_LINE_QUOTE = re.compile(r'''
    (             # Make the whole match a group so findall can return it
    [\S \t]*?     # any non line-break in front of it
    (["'])        # capture the start of the quote
    (?:[^\2].*?)  # characters not including the closing quote
    [^\\]\2       # end with a the opening quote, unescaped
    )
    ''', VERBOSE | MULTILINE | DOTALL)
RE_FUNCTION = re.compile(r'''
    (?:
    ^function\s+[\S]+(?:\s*\(\))?  # start with function name (maybe ())
    |
    ^[\S]+\s*\(\)                  # start with 'name()' or 'name ()'
    )
    [^\S\r\n]*\n?[^\S\r\n]*        # whitespace, maybe a newline
    {?\s*\n                        # maybe a { with space and or newlines there
    ''', MULTILINE | VERBOSE)


def get_range_string(items):
    '''Convert a list (or comma separated string) of numbers to a range string.

    Based on https://stackoverflow.com/q/9847601/8086281
    '''
    if isinstance(items, str):
        items = items.split(',')

    items = map(int, items)
    str_list = []
    for k, g in groupby(enumerate(items), lambda x: x[0]-x[1]):
        ilist = list(map(itemgetter(1), g))
        if len(ilist) > 1:
            str_list.append('{}-{}'.format(ilist[0], ilist[-1]))
        else:
            str_list.append('{}'.format(ilist[0]))
    return ', '.join(str_list)


def shell_strip_line_continuation(text):
    # Line continuation marks the last line the executed line
    text = RE_LINE_CONTINUATION_REMOVE.sub('', text)
    for match in RE_LINE_CONTINUATION.findall(text):
        text = _replace_multiline_string_filler_at_start(text, match)
    return text


def _replace_multiline_string_filler_at_start(text, match):
    return text.replace(match, FILLER + '\n' * match.count('\n'), 1)


def shell_strip_escaped_quotes(text):
    return RE_ESCAPED_QUOTE.sub('', text)


def shell_strip_comments(text):
    return RE_COMMENT.sub('', text)


def shell_strip_heredoc(text):
    d = [g[0] for g in RE_HEREDOC.findall(text)]
    for match in d:
        text = _replace_multiline_string_filler_at_start(text, match)
    return text


def shell_strip_function(text):
    for match in RE_FUNCTION.findall(text):
        text = text.replace(match, '\n' * match.count('\n'), 1)
    return text


def shell_strip_multiline_quotes(text):
    # The last line is classified as the line that was executed
    # As findall returns the matching group, take the first group which
    # has specifically been designed to be the full match.
    for match in [g[0] for g in RE_MULTI_LINE_QUOTE.findall(text)]:
        if '\n' in match:
            text = text.replace(match, '\n' * match.count('\n') + FILLER, 1)
    return text


def shell_strip_logic(text):
    return RE_LOGIC_OPERATOR.sub('', text)


def determine_display_widths(values):
    # Figure out the widths
    widths = [max(map(len, col)) for col in zip(*values)]
    header_widths = widths[:]
    header_widths[-1] = len(values[0][-1])
    return widths, header_widths


def get_line_info(actual_lines, seen_lines):
    column_values = [COLUMN_HEADINGS]
    problem_lines = {}
    for script in actual_lines:
        covered = seen_lines[script]
        need = actual_lines[script]
        unrecognised_lines = covered.difference(need)
        not_covered = need.difference(covered)
        column_values.append([script, str(len(need)), str(len(not_covered)),
                              str(100 * (len(need)
                                  - len(not_covered)) // len(need))
                              + '%',
                              get_range_string(sorted(not_covered))])
        problem_lines[script] = unrecognised_lines
    return column_values, problem_lines


def display_results(actual_lines, seen_lines):
    # Get the test coverage information
    column_values, problem_lines = get_line_info(actual_lines, seen_lines)

    # Calculate widths and values for each column
    widths, header_widths = determine_display_widths(column_values)

    # Print the results
    print('---- coverage ----')
    print('  '.join(val.ljust(width) for val, width in zip(column_values[0],
                                                           header_widths)))
    for row in column_values[1:]:
        print('  '.join(val.ljust(width) for val, width in zip(row, widths)))
        # Warn about any problem lines as these should be fixed in this script
        if problem_lines[row[0]]:
            print('**** lines reached that are not understood: ' +
                  get_range_string(sorted(problem_lines[row[0]])))


def get_test_results(test_scripts):
    # If stdin is not provided, assume a file is provided
    if sys.stdin.isatty():
        test_results = []
        use_env = os.environ.copy()
        use_env['PS4'] = DEFAULT_PS4

        for s in test_scripts:
            if not os.path.isfile(s):
                raise OSError('"{}" does not exist, aborting!'.format(s))
            proc = subprocess.Popen(BASE_CMD + [s],  # nosec
                                    env=use_env, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            proc.wait()
            test_results.append(tuple(map(lambda x: x.decode('utf-8'),
                                          proc.communicate())))
    else:
        test_results = [('', '\n'.join([l for l in sys.stdin]))]
    return test_results


def get_executed_lines(test_results):
    # Extract lines which have been executed
    script_lines = {}
    for r in test_results:
        err = r[1].splitlines()
        for line in err:
            line = str(line)
            if not (line.startswith('+')
                    and line.strip('+').startswith("PS4 + ")):
                continue
            _, script, duration, lineno, _ = line.split(" + ", 4)

            # Do not count the test script as a script
            if script in test_scripts:
                continue
            lineno = int(lineno.replace('L', ''))
            if script in script_lines:
                script_lines[script].add(lineno)
            else:
                script_lines[script] = {lineno}
    return script_lines


def get_lines_in_scripts(all_scripts):
    # Now check which lines matter
    lines_to_cover = {script: set() for script in all_scripts}

    for script in all_scripts:
        with open(script, 'r') as script_file:
            data = '\n'.join([l.strip() for l in script_file.readlines()])

        # Remove items that are not counted as lines. The order of these
        # operations does matter as the regex have not been designed to handle
        # all permutations individually

        # Remove escaped quotes
        data = shell_strip_escaped_quotes(data)

        # Remove comments from the script, replacing with empty strings
        data = shell_strip_comments(data)

        # Adjust line continuation
        data = shell_strip_line_continuation(data)

        # Remove heredoc
        data = shell_strip_heredoc(data)

        # Change functions to blank lines
        data = shell_strip_function(data)

        # change multi-line quoted things to a single line and blank lines
        data = shell_strip_multiline_quotes(data)

        # Remove logic operators that don't count as lines
        data = shell_strip_logic(data)

        enumerator = enumerate(data.splitlines())
        # Look at each line now
        for line_number, line in enumerator:
            # Ignore blank lines
            if not line:
                continue

            # Ignore open/closing loop block items
            lines_to_cover[script].add(line_number + 1)
    return lines_to_cover


def find_scripts(search_path):
    if os.path.isfile(search_path):
        return search_path
    results = []
    for suffix in ('sh', 'bash', 'ksh'):
        results.extend(Path(search_path).rglob(f'test_*.{suffix}'))
    return results


if __name__ == '__main__':
    # Get the paths to the test scripts
    try:
        test_paths = sys.argv[1:]
    except IndexError:
        test_paths = []
    test_scripts = []
    if not test_paths:
        test_paths = ['.']

    for p in test_paths:
        test_scripts.extend(find_scripts(p))

    test_results = get_test_results(test_scripts)
    script_lines = get_executed_lines(test_results)
    lines_to_cover = get_lines_in_scripts([s for s in script_lines])
    display_results(lines_to_cover, script_lines)
