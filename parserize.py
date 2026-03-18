
from nodes import *
from llvmlite.ir import IntType
from lexical import Token


class StepContext:
    def __init__(self, left, center):
        self.left = left
        self.sign = center

    def unpack(self):
        return self.left, self.sign
        

class Parser:
    def __init__(self, tokens:list[Token]):
        self.tokens = tokens
        self.cur_tok = tokens[0]
        self.cur_pos = 0


    def next_tok(self):
        self.cur_pos += 1

        if len(self.tokens) > self.cur_pos:
            self.cur_tok = self.tokens[self.cur_pos]

        else:
            self.cur_tok = None



    def expr(self):

        print("called expr")

        print("calling term for left")
        left = self.term()
        print(self.cur_tok)

        while (self.cur_tok != None
        and self.cur_tok.type in (
            T_ADD, T_SUB, T_MOD, T_RPAN1
        )):

            print("in loop, expr")

            if self.cur_tok.type == T_RPAN1:
                print("ret due to rpan1, expr")
                self.next_tok()
                return left

            
            center = self.cur_tok.type
            self.next_tok()

            print("calling term for right")
            right = self.term()
            print(self.cur_tok)

            left = BinOpNode(center, left, right)

        print("ret from expr",left)
        return left


    def term(self):

        print("called term")

        print("calling factor for left")
        left = self.factor()
        print(self.cur_tok)

        while (self.cur_tok != None
        and self.cur_tok.type in(
            T_MUL, T_DIV, T_RPAN1
        )):

            print("in loop, term")
        
            if self.cur_tok.type == T_RPAN1:
                print("ret due to rpan1, term")
                return left

            
            center = self.cur_tok.type
            self.next_tok()

            print("calling factor for right")
            right = self.factor()

            left = BinOpNode(center, left, right)

        print("ret from term", left)
        return left


    def factor(self):
        t = self.cur_tok

        if t == None or (not isinstance(t, Token)):
            raise Exception("expected more tokens")

        if t.type in (T_ADD, T_SUB):
            self.next_tok()
            res = self.factor()

            if t.type == T_SUB:
                return NegNode(res)

            else:
                return PosNode(res)
                

        elif t.type == T_LPAN1:
            self.next_tok()
            return self.expr()

        elif (t.type == T_LITERAL
        and t.typer == "intiger"):
        
            self.next_tok()
            const = ConstantNode(t.value, IntType(32))
            print("ret from factor", const, self.cur_tok)

            return const
            


    def parse(self):
        print("called parse")
        return self.expr()
            



        


