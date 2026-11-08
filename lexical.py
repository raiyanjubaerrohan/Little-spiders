from utils import (
    T_ADD,
    T_SUB,
    T_MUL,
    T_DIV,
    T_MOD,
    T_QUS,
    T_IDEN,
    T_LPAN1,
    T_LPAN2,
    T_LPAN3,
    T_RPAN1,
    T_RPAN2,
    T_RPAN3,
    T_KEY,
    T_NEQ,
    T_ARROW,
    T_COLON,
    T_COMMA,
    T_EOS,
    T_EQ,
    T_EQS,
    T_GTE,
    T_GT,
    T_LTE,
    T_LT,
    T_LITERAL,
    T_SQUTE,
    NUMBERS,
    ALPHABETS,
    keywords,
)

from diagnostical import Span, Diagnostics

class Token:
    def __init__(self, ty, pos: Span, val = 0, typ = 0):
        self.type = ty
        self.value = val
        self.typer = typ
        self.pos = pos

    def __repr__(self):
        if self.type == T_LITERAL:
            return f"{self.value}:{self.typer}=>{self.type}"

        if self.value:
            return f"{self.value}=>{self.type}"

        return f"{self.type}"

    def __eq__(self, other):
        return self.type == other

    def __ne__(self, other):
        return self.type != other


class Lexer:

    def __init__(self, text, diagctx):
        self.pos = -1
        self.text = text
        self.cur = None
        self.span_cur = -1
        self.ln = 0
        self.diagctx = diagctx
        self.next_chr()

    def next_chr(self):
        self.pos += 1
        self.span_cur += 1

        if len(self.text) > self.pos:
            self.cur = self.text[self.pos]
        else:
            self.cur = None

        #end

    def lex(self) -> list[Token] | None:

        tokens: list[Token] = []

        while self.cur is not None:

            if self.cur in ALPHABETS+'_':
                tokens.append(self.makeIdentifier())

            elif self.cur in NUMBERS:
                if res := self.makeNumber():
                    tokens.append(res)

            elif self.cur == ' ': #space char
                self.next_chr()

            elif self.cur == '\n': #new line
                self.ln += 1
                self.span_cur = -1
                self.next_chr()

            elif self.cur == '\t': #tab char
                self.next_chr()

            elif self.cur == '+':
                pos = Span((self.ln, self.span_cur), (self.ln+1, self.span_cur+1))
                tokens.append(Token(T_ADD, pos))
                self.next_chr()

            elif self.cur == '-':
                pos = Span((self.ln, self.span_cur), (self.ln+1, self.span_cur+1))
                tokens.append(Token(T_SUB, pos))
                self.next_chr()

            elif self.cur == '*':
                pos = Span((self.ln, self.span_cur), (self.ln+1, self.span_cur+1))
                tokens.append(Token(T_MUL, pos))
                self.next_chr()

            elif self.cur == '/':
                pos = Span((self.ln, self.span_cur), (self.ln+1, self.span_cur+1))
                tokens.append(Token(T_DIV, pos))
                self.next_chr()

            elif self.cur == '%':
                pos = Span((self.ln, self.span_cur), (self.ln+1, self.span_cur+1))
                tokens.append(Token(T_MOD, pos))
                self.next_chr()

            elif self.cur == '?':
                pos = Span((self.ln, self.span_cur), (self.ln+1, self.span_cur+1))
                tokens.append(Token(T_QUS, pos))
                self.next_chr()

            elif self.cur == ':':
                pos = Span((self.ln, self.span_cur), (self.ln+1, self.span_cur+1))
                tokens.append(Token(T_COLON, pos))
                self.next_chr()

            elif self.cur == ',':
                pos = Span((self.ln, self.span_cur), (self.ln+1, self.span_cur+1))
                tokens.append(Token(T_COMMA, pos))
                self.next_chr()

            elif self.cur in ('=','!'):
                if res := self.makeEqs():
                    tokens.append(res)

            elif self.cur == '<':
                tokens.append(self.makeLTorGT(T_LT))

            elif self.cur == '>':
                tokens.append(self.makeLTorGT(T_GT))

            elif self.cur == '(':
                pos = Span((self.ln, self.span_cur), (self.ln+1, self.span_cur+1))
                tokens.append(Token(T_LPAN1, pos))
                self.next_chr()

            elif self.cur == ')':
                pos = Span((self.ln, self.span_cur), (self.ln+1, self.span_cur+1))
                tokens.append(Token(T_RPAN1, pos))
                self.next_chr()

            elif self.cur == '{':
                pos = Span((self.ln, self.span_cur), (self.ln+1, self.span_cur+1))
                tokens.append(Token(T_LPAN2, pos))
                self.next_chr()

            elif self.cur == '}':
                pos = Span((self.ln, self.span_cur), (self.ln+1, self.span_cur+1))
                tokens.append(Token(T_RPAN2, pos))
                self.next_chr()

            elif self.cur == '[':
                pos = Span((self.ln, self.span_cur), (self.ln+1, self.span_cur+1))
                tokens.append(Token(T_LPAN3, pos))
                self.next_chr()

            elif self.cur == ']':
                pos = Span((self.ln, self.span_cur), (self.ln+1, self.span_cur+1))
                tokens.append(Token(T_RPAN3, pos))
                self.next_chr()

            elif self.cur == '"':
                string, err = self.makeString()
                if err: return None, err
                tokens.append(string)

            elif self.cur == "'":

                start = (self.ln, self.span_cur)
                self.next_chr() # consume the '

                if res := self.makeEscapeSequence():
                    tokens.append(Token(
                        T_SQUTE,
                        Span(start, (self.ln+1, self.span_cur+1)),
                        res,
                        "char"
                    ))

                else:
                    tokens.append(Token(
                        T_SQUTE,
                        Span(start, (self.ln+1, self.span_cur+1)),
                        self.cur,
                        "char"
                    ))

                # common
                self.next_chr()
                self.next_chr()
                # we need it twich because one for the actual char
                # and one for the single quote

            elif self.cur == ";":
                pos = Span((self.ln, self.span_cur), (self.ln+1, self.span_cur+1))
                tokens.append(Token(T_EOS, pos))
                self.next_chr()

            # comment remover
            elif self.cur == "#":
                while self.cur not in ('\n','', None): self.next_chr()
                self.next_chr() #to escape the \n or eof

            else:
                self.diagctx.emit(Diagnostcs(
                    f"unknown symbol '{self.cur}' is used",
                    "L0638",
                    Span((self.ln, self.span_cur), (self.ln+1, self.span_cur+1)),
                    "remove this"
                ))

                self.next_chr()

        return tokens
        #end

    def makeLTorGT(self, toktype):
        start_pos = (self.ln, self.span_cur)
        self.next_chr()

        if self.cur == '=':
            self.next_chr()
            pos = Span(start_pos, (self.ln+1, self.span_cur+1))
            return Token(toktype+"E", pos)

        pos = Span(start_pos, (self.ln+1, self.span_cur+1))
        return Token(toktype, pos)

    def makeEqs(self):
        eqs = ''
        start_pos = (self.ln, self.span_cur)

        while (self.cur is not None
        and self.cur in ('=','>','!')):
            eqs += self.cur
            self.next_chr()

        pos = Span(start_pos, (self.ln+1, self.span_cur+1))

        if eqs == '=':
            return Token(T_EQ, pos)

        if eqs == '==':
            return Token(T_EQS, pos)

        if eqs == '!=':
            return Token(T_NEQ, pos)

        if eqs == '=>':
            return Token(T_ARROW, pos)

        self.diagctx.emit(Diagnostics(
            f"unknown symbol '{eqs}' is used",
            "L0647",
            pos,
            smsg="currect this"
        ))
        
        return None

    def makeNumber(self):
        num_str = ''
        dots = 0
        have_error = False
        start_pos = (self.ln, self.span_cur)

        while (self.cur is not None
        and self.cur in NUMBERS+'.'):

            if self.cur == '.': dots+= 1
            if dots > 1: have_error = True

            num_str += self.cur
            self.next_chr()

        pos = Span(start_pos, (self.ln+1, self.span_cur+1))

        if have_error:
            self.diagctx.emit(Diagnostcs(
                f"invalid number {num_str} with many dots",
                "L0650",
                pos,
                "remove the extra dots"
            ))

            return None

        if dots == 1:
            return Token(T_LITERAL, pos, float(num_str), "float")

        return Token(T_LITERAL, pos, int(num_str), "int")

    def makeString(self):
        start_pos = (self.ln, self.span_cur)
        self.next_chr()
        string = ''

        while self.cur not in (None, '"'):

            if res := self.makeEscapeSequence():
                string += res
            else:
                string += self.cur

            self.next_chr()

        self.next_chr()

        pos = Span(start_pos,(self.ln+1, self.span_cur+1))

        return Token(T_LITERAL, pos, str(string), "string"), None

    def makeEscapeSequence(self):

        start_pos = (self.ln, self.span_cur)

        if self.cur == '\\':
            self.next_chr()

            if self.cur == 'n': return '\n'
            if self.cur == 't': return '\t'
            if self.cur == '"': return '\''
            if self.cur == "'": return '\"'
            if self.cur == '\\': return '\\'

            span = Span(start_pos, (self.ln+1, self.span_cur+1))
            self.diagctx.emit(Diagnostics(
                f"invalid escape sequence '\\{self.cur}' is used",
                "L0663",
                span,
                "remove this"
            ))

        return None

    def makeIdentifier(self):
        iden = ''

        start_pos = (self.ln, self.span_cur)

        while (self.cur is not None
        and self.cur in ALPHABETS+'_'+NUMBERS):
            iden += self.cur

            self.next_chr()

        pos = Span(start_pos, (self.ln+1, self.span_cur+1))

        if iden in keywords:
            return Token(T_KEY, pos, str(iden))

        if iden in ("true", "false"):
            return Token(
                T_LITERAL,
                pos,
                iden == "true",
                "bool"
            )

        return Token(T_IDEN, pos, str(iden))
