from utils import *

class Token:
    def __init__(self, ty, pos: Position, val = 0, typ = 0):
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

    def __init__(self):
        self.pos = 0
        self.text = ""
        self.cur = None

    def next_chr(self):
        self.pos += 1

        if len(self.text) > self.pos:
            self.cur = self.text[self.pos]
        else:
            self.cur = None

        #end

    def lex(self, text: str) -> tuple[list[Token] | None, Exception | None]:
    
        tokens: list[Token] = []
        self.text = text
        self.pos = -1
        self.cur = None
        
        self.next_chr()

        while self.cur != None:

            if self.cur in ALPHABETS+'_':
                tokens.append(self.makeIdentifier())

            elif self.cur in NUMBERS:
                res, err = self.makeNumber()
                if err: return None, err

                tokens.append(res)

            elif self.cur == ' ': #space char
                self.next_chr()

            elif self.cur == '\n': #new line
                self.next_chr()

            elif self.cur == '\t': #tab char
                self.next_chr()
            
            elif self.cur == '+':
            	pos = Position(self.pos, self.pos+1)
            	tokens.append(Token(T_ADD, pos))
            	self.next_chr()

            elif self.cur == '-':
            	pos = Position(self.pos, self.pos+1)
            	tokens.append(Token(T_SUB, pos))
            	self.next_chr()

            elif self.cur == '*':
            	pos = Position(self.pos, self.pos+1)
            	tokens.append(Token(T_MUL, pos, 1))
            	self.next_chr()
            	
            elif self.cur == '/':
                pos = Position(self.pos, self.pos+1)
                tokens.append(Token(T_DIV, pos, 1))
                self.next_chr()
                
            elif self.cur == '?':
                pos = Position(self.pos, self.pos+1)
                tokens.append(Token(T_QUS, pos))
                self.next_chr()

            elif self.cur == ':':
                pos = Position(self.pos, self.pos+1)
                tokens.append(Token(T_COLON, pos))
                self.next_chr()

            elif self.cur in ('=','!'):
                res, err = self.makeEqs()
                if err: return None, err
                tokens.append(res)

            elif self.cur == '<':
                tokens.append(self.makeLT())

            elif self.cur == '>':
                tokens.append(self.makeGT())

            elif self.cur == '(':
                pos = Position(self.pos, self.pos+1)
                tokens.append(Token(T_LPAN1, pos))
                self.next_chr()

            elif self.cur == ')':
                pos = Position(self.pos, self.pos+1)
                tokens.append(Token(T_RPAN1, pos))
                self.next_chr()

            elif self.cur == '{':
                pos = Position(self.pos, self.pos+1)
                tokens.append(Token(T_LPAN2, pos))
                self.next_chr()

            elif self.cur == '}':
                pos = Position(self.pos, self.pos+1)
                tokens.append(Token(T_RPAN2, pos))
                self.next_chr()

            elif self.cur == '[':
                pos = Position(self.pos, self.pos+1)
                tokens.append(Token(T_LPAN3, pos))
                self.next_chr()

            elif self.cur == ']':
                pos = Position(self.pos, self.pos+1)
                tokens.append(Token(T_RPAN3, pos))
                self.next_chr()

            elif self.cur == '"':
                tokens.append(self.makeString())

            elif self.cur == "'":
                pos = Position(self.pos, self.pos+1)
                tokens.append(Token(T_SQUTE, pos))
                self.next_chr()


            elif self.cur == ";":
                pos = Position(self.pos, self.pos+1)
                tokens.append(Token(T_EOS, pos))
                self.next_chr()

            else: 
                return None, Exception(
                    f"invalid token '{self.cur}''"
                )


        return tokens, None
        #end

    def makeLT(self):
        start_pos = self.pos
        self.next_chr()

        if self.cur == '=':
            self.next_chr()
            pos = Position(start_pos, self.pos)
            return Token(T_LTE, pos)

        pos = Position(start_pos, self.pos)
        return Token(T_LT, pos)


    def makeGT(self):
        start_pos = self.pos
        self.next_chr()

        if self.cur == '=':
            self.next_chr()
            pos = Position(start_pos, self.pos)
            return Token(T_GTE, pos)

        pos = Position(start_pos, self.pos)
        return Token(T_GT, pos)
                
        

    def makeEqs(self):
        eqs = ''
        start_pos = self.pos

        while (self.cur != None
        and self.cur in ('=','>','!')):
            eqs += self.cur
            self.next_chr()

        pos = Position(start_pos, self.pos)

        if eqs == '=':
            return Token(T_EQ, pos), None

        elif eqs == '==':
            return Token(T_EQS, pos), None

        elif eqs == '!=':
            return Token(T_NEQ, pos),  None

        elif eqs == '=>':
            return Token(T_ARROW, pos), None

        else:
            return None, Exception(
                f"invalid token {eqs}"
            )

    def makeNumber(self):
        num_str = ''
        dots = 0
        have_error = False
        start_pos = self.pos

        while (self.cur != None 
        and self.cur in NUMBERS+'.'):
            
            if self.cur == '.': dots+= 1
            if dots > 1: have_error = True

            num_str += self.cur
            self.next_chr()

        pos = Position(start_pos, self.pos)
        
        if have_error:
            return None, Exception(
                f"invalid number {num_str}"
            )

        elif dots == 1:
            return Token(T_LITERAL, pos, float(num_str), "float"), None

        else:
            return Token(T_LITERAL, pos, int(num_str), "int"), None


        #end


    def makeString(self):
        start_pos = self.pos
        self.next_chr()
        string = ''
        
        while self.cur not in (None, '"'):
            
            string += self.cur
            self.next_chr()
            

        self.next_chr()

        pos = Position(start_pos, self.pos)

        return Token(T_LITERAL, pos, str(string), "string")


    def makeIdentifier(self):
        iden = ''
        
        start_pos = self.pos

        while (self.cur != None 
        and self.cur in ALPHABETS+'_'+NUMBERS):
            iden += self.cur

            self.next_chr()
            
        pos = Position(start_pos, self.pos)

        if iden in keywords:
            return Token(T_KEY, pos, str(iden))

        if iden in ("true", "false"):
            return Token(T_LITERAL, pos, str(iden), "bool")

        return Token(T_IDEN, pos, str(iden))
