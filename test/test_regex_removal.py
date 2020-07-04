import unittest

import shell_cov.shell_cov as shell_cov

from . import test_expected_results

RAW_TEXT = '\n'.join(s.strip() for s in r'''
#!/bin/bash
set -eux -o pipefail
arg=$1
values=(1 2 3 4 5)
echo "num values = ${#values[@]}"

case "$arg" in
    1|2|${#values[@]}) echo result!!!
    ;;
    25) # do nothing here
    ;;
    *) ;;
esac; echo hello

case "$arg"
    in
    8) echo testing;;
esac

if (( arg == ${#values[@]} ))
    then
    # do something
    echo awktest |
        awk '{
            print $1
        }'
fi
if [[ 1 == 1]]; then :;;;; fi

;;; #
;;;
cat <<- EOF
EOF hello
hello EOF
EOF
cat <<-EOF
EOF
cat <<'EOF'
EOFI
EOF

echo hello \
        test \
        boo \
\ #test
\



echo hello \\

echo "multi-line
string"
echo 'multi-line
single quote string
'
echo 'escaped
\'multi-single\''
echo "escaped
\"multi-double
\"

"


function one {
 # do something
 :;;
    }
function two() {
test; }

function three ()
{

:

}

four()
{
:
}
five() { testing; }
six() { testing;;;;;;; ;; ;;
}
'''.splitlines())


class TestRegex(unittest.TestCase):
    def test_shell_strip_escaped_quotes(self):
        self.assertEqual(shell_cov.shell_strip_escaped_quotes(RAW_TEXT),
                         test_expected_results.ESCAPED_QUOTES)

    def test_shell_strip_comments(self):
        # Comment removal does not remove leading whitespace. To simplify
        # comparison in the test, strip it all
        actual = shell_cov.shell_strip_comments(RAW_TEXT)
        self.assertEqual('\n'.join(s.strip() for s in actual.splitlines()),
                         test_expected_results.COMMENTS)

    def test_shell_strip_line_continuation(self):
        self.assertEqual(shell_cov.shell_strip_line_continuation(RAW_TEXT),
                         test_expected_results.LINE_CONTINUATION)

    def test_shell_strip_heredoc(self):
        self.assertEqual(shell_cov.shell_strip_heredoc(RAW_TEXT),
                         test_expected_results.HEREDOC)

    def test_shell_strip_function(self):
        self.assertEqual(shell_cov.shell_strip_function(RAW_TEXT),
                         test_expected_results.FUNCTION)

    def test_shell_strip_multiline_quotes(self):
        self.assertEqual(shell_cov.shell_strip_multiline_quotes(RAW_TEXT),
                         test_expected_results.MULTILINE_QUOTES)

    def test_shell_strip_logic(self):
        self.assertEqual(shell_cov.shell_strip_logic(RAW_TEXT),
                         test_expected_results.LOGIC)
