
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
    
        left, err = self.term()

        if err: return None, err

        while (self.cur_tok != T_EOS
        and self.cur_tok.type in (
            T_ADD, T_SUB, T_MOD, T_RPAN1
        )):


            if self.cur_tok == T_RPAN1:
                self.next_tok()
                return left, None

            
            center = self.cur_tok.type
            self.next_tok()

            right, err = self.term()

            if err: return None, err

            left = BinOpNode(center, left, right)
            
        return left, None


    def term(self):

        left, err = self.factor()

        if err: return None, err

        while (self.cur_tok != T_EOS
        and self.cur_tok.type in(
            T_MUL, T_DIV, T_RPAN1
        )):

        
            if self.cur_tok == T_RPAN1:
                return left, None

            
            center = self.cur_tok.type
            self.next_tok()

            right, err = self.factor()

            if err: return None, err

            left = BinOpNode(center, left, right)
            
        return left, None


    def factor(self):
        t = self.cur_tok

        if t == T_EOS or (not isinstance(t, Token)):
            return None,Exception("expected more tokens")

        if t.type in (T_ADD, T_SUB):
            self.next_tok()
            res = self.factor()

            if t == T_SUB:
                return NegNode(res),None

            else:
                return PosNode(res), None
                

        elif t == T_LPAN1:
            self.next_tok()
            return self.expr(), None

        elif (t == T_LITERAL
        and t.typer in ("intiger","float")):
        
            self.next_tok()
            return ConstantNode(t.value, t.typer), None


        return None, Exception(f"invalid token {t}")



    def expect(self, *v, isType = True):

        if isType:
            if not self.cur_tok.type in  v:
                return Exception(
                    f"error, expected {v}"
                )

        else:
            if not self.cur_tok.value in v:
                return Exception(
                    f"error, expected {v} as value"
                )

        return None

            

    def parse(self):

        if self.cur_tok.value == "let":

            self.next_tok()

            if err := self.expect(T_IDEN):
                return None, err
            
            var_name = self.cur_tok.value
            var_type = 0
            var_expr = 0
            
            self.next_tok()

            if self.cur_tok == T_COLON:
                self.next_tok()

                if err := self.expect("int","float",isType=False):
                    return None, err

                var_type = self.cur_tok.value
                self.next_tok()

            if self.cur_tok == T_EQ:
                self.next_tok()

                var_expr, err = self.expr()

                if err: return None, err

            
            if (not var_expr) and (not var_type):
                return None, Exception(f"excepted a type or an default value, {var_name}")

            varDecNode = VarDeclareNode(var_name)


            if var_expr:
                varDecNode.expr = var_expr
            else:
                varDecNode.expr = ConstantNode(0, "intiger")


            if var_type:
                varDecNode.llvm_type = var_type

            return varDecNode, None
                
        return None, None

    #end function
    
#end class
        
