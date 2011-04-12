#!/bin/bash
PACKAGE=$1; shift
MODULE=$1; shift
if [ $MODULE == __init__ ]; then
	cat >__init__.py <<EOF
# Import everything from $PACKAGE for backwards compatibility.
globals().update(dict(__import__('$PACKAGE', [], [], 'hack').__dict__, __path__=__path__))
EOF
else
	cat >${MODULE}.py <<EOF
# Import everything from $PACKAGE.$MODULE for backwards compatibility.
globals().update(__import__('$PACKAGE.$MODULE', [], [], 'hack').__dict__)
EOF
fi
