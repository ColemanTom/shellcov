import argparse
import os
import re
import subprocess  # nosec
import sys
from itertools import groupby
from pathlib import Path
from operator import itemgetter
from re import DOTALL, MULTILINE, VERBOSE
from typing import Dict, List, Union

VERSION = '0.0.0'

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
    [\S \t]*?     # any non line-break in front of the quote
    (["'])        # capture the start of the quote
    (?:[^\2]*?)   # characters not including the closing quote
    [^\\]?\2      # end with the opening quote, unescaped
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


def parse_args(args: List[str]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Generate shell coverage information.",
        epilog=f"""
If you are running this using existing script outputs, ensure your PS4 is correct.
export PS4='{DEFAULT_PS4}'

NOTE: For BASH, prior to v4.3alpha, PS4 gets truncated to 99 characters.
      You will need to override the BASH_SOURCE in this file's DEFAULT_PS4 variable
      to strip out some of the path from the script.
      e.g. ${{BASH_SOURCE/some_path//script}}

ShellCov Version = v{VERSION}
"""
    )

    # Allow users to specify some script/path options
    parser.add_argument("--only-paths", "-p", nargs="+", help="Space separated list of paths. Only scripts whose paths start with this prefix will be analysed.\nThis helps filter out scripts which should not be analysed because they belong to a different library.", metavar='PATH')
    parser.add_argument("--ignore-paths", nargs="+", help="Space separated list of paths to ignore. Any script which matches part of this will be ignored.", metavar='PATH')
    parser.add_argument("--replace-paths", nargs="+", help="Space separated list of colon separated paths. The left hand side is the original path prefix, the right hand side what to replace it with. This can be useful to work around bugs in BASH prior to 4.3alpha or when you are running the script on a different platform to where results are being analysed. E.g. --replace-paths /a/b/c/run:/home /a/b/c/d/run:/data", metavar='ORIG:REPLACE')

    # Choose multiple ways to analyse results
    group = parser.add_argument_group(title="Chose one of:")
    exclusive_group = group.add_mutually_exclusive_group(required=True)
    exclusive_group.add_argument("--test-paths", "-t", nargs="+", help="Space separated list of directories to search in for test scripts, or, test scripts to run. Test script filenames must start with 'test_'", metavar='TEST_SCRIPT')
    exclusive_group.add_argument("--canned-results", "-r", nargs="+", help="Space separated list of pre-generated outputs to analyse", metavar='RESULT')
    return parser.parse_args(args)


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
            # TODO: Strip out the test script from the output
            test_results.append(tuple(map(lambda x: x.decode('utf-8'),
                                          proc.communicate())))
    else:
        test_results = [('', '\n'.join([l for l in sys.stdin]))]
    return test_results


def get_executed_lines(test_results, path_include: List[str] =None, path_ignore:List[str]=None,path_replace: List[str] =None):
    # Extract lines which have been executed
    script_lines = {}
    for r in test_results:
        err = r[1].splitlines()
        for line in err:
            line = str(line)
            if not (line.startswith('+')
                    and line.strip('+').startswith("PS4 + ")):
                continue
            _, script, duration, line_number, _ = line.split(" + ", 4)

            # If this path hasn't been included in the allow list, ignore it
            if path_include is not None and not any(p in script for p in path_include):
                # TODO: Insert log.debug informing that this script is being ignored
                continue

            # If this script is in the ignore list, skip
            if path_ignore is not None and any(p in script for p in path_ignore):
                # TODO: Insert log.debug informing that this script is being ignored
                continue

            # Update the script path if required by the command line arguments.
            # This might have been done because the location the script was run was
            # different to where the coverage analysis is taking place, or because of
            # bugs in BASH prior to 4.3alpha.
            if path_replace is not None:
                for p in path_replace:
                    search, replacement = p.split(':', maxsplit=1)
                    script = script.replace(search, replacement)

            # Update the scripts dictionary with the line number
            line_number = int(line_number.replace('L', ''))
            if script in script_lines:
                script_lines[script].add(line_number)
            else:
                script_lines[script] = {line_number}
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


def run_test_scripts(test_paths: List[str], path_include: List[str] =None,path_ignore:List[str]=None, path_replace: List[str] =None) -> Dict[str, int]:
    test_scripts = []

    for p in test_paths:
        test_scripts.extend(find_scripts(p))

    test_results = get_test_results(test_scripts)
    return get_executed_lines(output, path_include, path_ignore, path_replace)


def get_script_lines_from_canned_results(canned_results: List[str],path_include: List[str] =None,path_ignore:List[str]=None, path_replace: List[str] =None) -> Dict[str, int]:
    output = [_read_canned_results(p) for p in canned_results]
    return get_executed_lines(output, path_include, path_ignore, path_replace)


def _read_canned_results(canned_result: str) -> str:
    with open(canned_result) as f:
         return ('', f.read())


if __name__ == '__main__':
    args = parse_args(sys.argv[1:])
    if args.test_paths is not None:
        # We need to run the test scripts to collect results
        script_lines = run_test_scripts(args.test_paths, args.only_paths, args.ignore_paths, args.replace_paths)
    else:
        # Canned results must have been provided
        script_lines = get_script_lines_from_canned_results(args.canned_results, args.only_paths, args.ignore_paths, args.replace_paths)

    lines_to_cover = get_lines_in_scripts([s for s in script_lines])
    display_results(lines_to_cover, script_lines)
