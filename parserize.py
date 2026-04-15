
from nodes import *
from utils import T_EOS, variables_ptr
from llvmlite.ir import IntType
from llvmlite.ir import HalfType, FloatType, DoubleType
from llvmlite.ir import PointerType, VoidType
from lexical import Token
from utils import T_IDEN

        

class Parser:
    def __init__(self, tokens:list[Token]):
        self.tokens = tokens
        self.cur_tok = tokens[0]
        self.cur_pos = 0
        self.cur_node = 0


    def next_tok(self):
        self.cur_pos += 1

        if len(self.tokens) > self.cur_pos:
            self.cur_tok = self.tokens[self.cur_pos]

        else:
            self.cur_tok = None



    def expr(self):
    
        left = self.term()

        while (self.cur_tok != T_EOS
        and self.cur_tok.type in (
            T_ADD, T_SUB, T_MOD, T_RPAN1
        )):


            if self.cur_tok == T_RPAN1:
                self.next_tok()
                return left

            
            center = self.cur_tok.type
            self.next_tok()

            right = self.term()

            left = BinOpNode(center, left, right)
            
        return left


    def term(self):

        left = self.factor()

        while (self.cur_tok != T_EOS
        and self.cur_tok.type in(
            T_MUL, T_DIV, T_RPAN1
        )):

        
            if self.cur_tok == T_RPAN1:
                return left

            
            center = self.cur_tok.type
            self.next_tok()

            right = self.factor()

            left = BinOpNode(center, left, right)
            
        return left


    def factor(self):
        t = self.cur_tok

        if t == T_EOS or (not isinstance(t, Token)):
            raise Exception("expected more tokens")

        if t.type in (T_ADD, T_SUB):
            self.next_tok()
            res = self.factor()

            if t == T_SUB:
                return NegNode(res)

            else:
                return PosNode(res)
                

        elif t == T_LPAN1:
            self.next_tok()
            return self.expr()

        elif (t == T_LITERAL
        and t.typer in ("intiger","float")):
        
            self.next_tok()
            const = ConstantNode(t.value, t.typer)
            return const



    def expect(self, v: tuple, /, isType = True):

        if isType:
            if not self.cur_tok.type in  v:
                raise Exception(
                    f"error, expected {v}"
                )

        else:
            if not self.cur_tok.value in v:
                raise Exception(
                    f"error, expected {v} as value"
                )

        return None

            

    def parse(self):

        if self.cur_tok.value == "let":

            self.next_tok()

            self.expect((T_IDEN))
            
            var_name = self.cur_tok.value
            var_type = 0
            var_expr = 0
            
            self.next_tok()

            if self.cur_tok == T_COLON:
                self.next_tok()

                self.expect(
                    ("int","float"),
                    isType=False
                )

                var_type = self.cur_tok.value
                self.next_tok()

            if self.cur_tok == T_EQ:
                self.next_tok()

                var_expr = self.expr()

            
            if (not var_expr) and (not var_type):
                raise Exception(f"excepted a type or an default value, {var_name}")

            varDecNode = VarDeclareNode(var_name)

            if var_expr:
                varDecNode.expr = var_expr

            if var_type:
                varDecNode.llvm_type = var_type

            return varDecNode
                
        return False

        

            
                

            
            



    
