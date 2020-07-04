from string import Template

from shell_cov.shell_cov import FILLER

ESCAPED_QUOTES = '\n'.join(s.strip() for s in r'''
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
multi-single'
echo "escaped
multi-double


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

COMMENTS = '\n'.join(s.strip() for s in r'''

set -eux -o pipefail
arg=$1
values=(1 2 3 4 5)
echo "num values = ${#values[@]}"

case "$arg" in
    1|2|${#values[@]}) echo result!!!
    ;;
    25)
    ;;
    *) ;;
esac; echo hello

case "$arg"
    in
    8) echo testing;;
esac

if (( arg == ${#values[@]} ))
    then

    echo awktest |
        awk '{
            print $1
        }'
fi
if [[ 1 == 1]]; then :;;;; fi

;;;
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
\
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

LINE_CONTINUATION = Template('\n'.join(s.strip() for s in r'''
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

${filler}







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
'''.splitlines())).safe_substitute({'filler': FILLER})

HEREDOC = Template('\n'.join(s.strip() for s in r'''
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
cat ${filler}



cat ${filler}

cat ${filler}



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
'''.splitlines())).safe_substitute({'filler': FILLER})

FUNCTION = Template('\n'.join(s.strip() for s in r'''
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



 # do something
 :;;
    }

test; }




:

}



:
}
five() { testing; }
six() { testing;;;;;;; ;; ;;
}
'''.splitlines())).safe_substitute({'filler': FILLER})

MULTILINE_QUOTES = Template('\n'.join(s.strip() for s in r'''
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


${filler}
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


${filler}


${filler}

${filler}




${filler}


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
'''.splitlines())).safe_substitute({'filler': FILLER})

LOGIC = '\n'.join(s.strip() for s in r'''
#!/bin/bash
set -eux -o pipefail
arg=$1
values=(1 2 3 4 5)
echo "num values = ${#values[@]}"

case "$arg" in
    1|2|${#values[@]}) echo result!!!

    25) # do nothing here


esac; echo hello

case "$arg"

    8) echo testing;;


if (( arg == ${#values[@]} ))

    # do something
    echo awktest |
        awk '{
            print $1
        }'

if [[ 1 == 1]]; then :;;;; fi

;;; #

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

function two() {
test; }

function three ()


:



four()

:

five() { testing; }
six() { testing;;;;;;; ;; ;;

'''.splitlines())
