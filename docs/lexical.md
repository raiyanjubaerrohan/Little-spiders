# The Lexer
the lexer is an essential part of a compiler. It scans the raw tokens and 
converts them to meaningfull tokens so the parser can parse those.
the lexer is the very first layer.

## the architechture
the lexer architechture is very simple. It has a function called 'lex',
inside it is a loop. It keeps going until it encounters a None.
It has two cursors that keep track of the currect position and current char.
It compares every possible tokens and then procide to the next char.
In simple words, it scans the text char by char and builds out tokens with
info about the type, the value and it's appoximate typer (e.g. int, float, string)
