from utils import *

class Token:

    def __init__(self, ty, val = 0, typ = 0):
        self.type = ty
        self.value = val
        self.typer = typ
        

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
    def __init__(self, text:str):
        self.text:str = text
        self.pos:int = 0
        self.cur:chr = text[0]
        self.tokens = None

    def next_chr(self):
        self.pos += 1

        if len(self.text) > self.pos:
            self.cur = self.text[self.pos]
        else:
            self.cur = None

        #end

    def lex(self):
        tokens: list[Token] = []

        if self.tokens: return self.tokens, None

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
                tokens.append(Token(T_ADD))
                self.next_chr()

            elif self.cur == '-':
                tokens.append(Token(T_SUB))
                self.next_chr()

            elif self.cur == '*':
                tokens.append(Token(T_MUL, 1))
                self.next_chr()

            elif self.cur == '/':
                tokens.append(Token(T_DIV, 1))
                self.next_chr()

            elif self.cur == '?':
                tokens.append(Token(T_QUS))
                self.next_chr()

            elif self.cur == ':':
                tokens.append(Token(T_COLON))
                self.next_chr()

            elif self.cur == '=':
                res, err = self.makeEqs()
                if err: return None, err

                tokens.append(res)

            elif self.cur == '<':
                tokens.append(self.makeLT())

            elif self.cur == '>':
                tokens.append(self.makeGT())

            elif self.cur == '(':
                tokens.append(Token(T_LPAN1))
                self.next_chr()

            elif self.cur == ')':
                tokens.append(Token(T_RPAN1))
                self.next_chr()

            elif self.cur == '{':
                tokens.append(Token(T_LPAN2))
                self.next_chr()

            elif self.cur == '}':
                tokens.append(Token(T_RPAN2))
                self.next_chr()

            elif self.cur == '[':
                tokens.append(Token(T_LPAN3))
                self.next_chr()

            elif self.cur == ']':
                tokens.append(Token(T_RPAN3))
                self.next_chr()

            elif self.cur == '"':
                self.next_chr()
                tokens.append(self.makeString())

            elif self.cur == "'":
                tokens.append(Token(T_SQUTE))
                self.next_chr()


            elif self.cur == ";":
                tokens.append(Token(T_EOS))
                self.next_chr()

            else: 
                return None, Exception(
                    f"invalid token '{self.cur}''"
                )

        self.tokens = tokens

        return tokens, None
        #end

    def makeLT(self):
        self.next_chr()

        if self.cur == '=':
            self.next_chr()
            return Token(T_LTE)

        return Token(T_LT)


    def makeGT(self):
        self.next_chr()

        if self.cur == '=':
            self.next_chr()
            return Token(T_GTE)

        return Token(T_GE)
                
        

    def makeEqs(self):
        eqs = ''

        while (self.cur != None
        and self.cur in ('=','>','?')):
            eqs += self.cur
            self.next_chr()

        if eqs == '=':
            return Token(T_EQ), None

        elif eqs == '=>':
            return Token(T_ARROW), None

        else:
            return None, Exception(
                f"invalid token {eqs}"
            )

        

    def makeNumber(self):
        num_str = ''
        dots = 0
        have_error = False

        while (self.cur != None 
        and self.cur in NUMBERS+'.'):
            if self.cur == '.': dots+= 1
            if dots > 1: have_error = True

            num_str += self.cur
            self.next_chr()


        if have_error:
            return None, Exception(
                f"invalid number {num_str}"
            )

        elif dots == 1:
            return Token(T_LITERAL, float(num_str), "float"), None

        else:
            return Token(T_LITERAL, int(num_str), "intiger"), None


        #end


    def makeString(self):
    
        string = ''
        
        while self.cur not in (None, '"'):
            
            string += self.cur
            self.next_chr()
            

        self.next_chr()

        return Token(T_LITERAL, str(string), "string")


    def makeIdentifier(self):
        iden = ''

        while (self.cur != None 
        and self.cur in ALPHABETS+'_'+NUMBERS):
            iden += self.cur

            self.next_chr()


        if iden in keywords:
            return Token(T_KEY, str(iden))

        return Token(T_IDEN, str(iden))
            

        
                

