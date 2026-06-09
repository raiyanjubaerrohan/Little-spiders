from nodes import *
from utils import T_EOS, variables_ptr, T_IDEN, T_EQ, cutOut
from utils import T_EQS, T_NEQ, T_LT, T_LTE, T_GT, T_GTE
from utils import T_KEY
from lexical import Token
from typing import Any

class Parser:

    def __init__(self):
        self.tokens:list[Token] = []
        self.cur_tok = None
        self.cur_pos = 0
        self.node_start = 0
        self.EOE = T_EOS


    def consume(self, tokens:list[Token]):
        for tok in tokens:
            self.tokens.append(tok)


    def next_tok(self):
        self.cur_pos += 1

        if len(self.tokens) > self.cur_pos:
            self.cur_tok = self.tokens[self.cur_pos]

        else:
            self.cur_tok = None

    def compare_expr(self):
        left, err = self.expr()

        if err: return None, err

        while (self.cur_tok != self.EOE
        and self.cur_tok.type in (
            T_EQS, T_NEQ, T_LT, T_LTE, T_GT, T_GTE
        )):

            if self.cur_tok == T_RPAN1:
                self.next_tok()
                return left, None

            center = self.cur_tok.type
            self.next_tok()

            right, err = self.expr()
            if err: return None, err
            left = CompareNode(center, left, right)

        return left, None


    def expr(self):

        left, err = self.term()

        if err: return None, err

        while (self.cur_tok != self.EOE
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

        while (self.cur_tok != self.EOE
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
            return "needed", Exception("expected more tokens")

        if t.type in (T_ADD, T_SUB):
            self.next_tok()
            res, err = self.factor()

            if err:
                return None, err

            if t == T_SUB:
                return NegNode(res),None

            else:
                return PosNode(res), None


        elif t == T_LPAN1:
            self.next_tok()
            return self.compare_expr()

        elif t == T_LITERAL:
            #a common factor
            self.next_tok()

            if t.typer in ("int","float"):
                return ConstantNode(t.value, t.typer), None

            elif t.typer == "bool":
                return ConstantNode(1 if t.value == "true" else 0, "bool"), None


        elif t == T_IDEN:

            iden = t.value
            self.next_tok()

            if self.cur_tok == T_LPAN1:
                pass #this is a call

            #else
            if iden in variables_ptr:

                return VarFetchNode(
                    variables_ptr[iden]["value"],
                    variables_ptr[iden]["type"]
                ), None

            else:
                return None, Exception(f"unknown variable {iden}")


        return None, Exception(f"invalid token {t}")



    def expect(self, *v, isType = True):

        if isType:
            if not self.cur_tok.type in v:
                return Exception(
                    f"expected {v}"
                )

        else:
            if not self.cur_tok.value in v:
                return Exception(
                    f"expected {v} as value"
                )

        return None

    def parse_var(self):

        self.next_tok()

        if self.cur_tok == None and self.cur_tok != T_EOS:
            return "needed", None

        if err := self.expect(T_IDEN):
            return None, err

        var_name = self.cur_tok.value
        var_type = 0
        var_expr = 0

        self.next_tok()

        if self.cur_tok == T_COLON:
            self.next_tok()

            if self.cur_tok == None and self.cur_tok != T_EOS:
                return "needed", None

            if err := self.expect(
                "int", "char", "short", "bool", #integer types
                "float", "double", #floating point types
                isType=False
            ): return None, err

            var_type = self.cur_tok.value
            self.next_tok()

        if self.cur_tok == T_EQ:
            self.next_tok()

            var_expr, err = self.compare_expr()

            if var_expr == "needed": return "needed", None
            if err: return None, err

        if self.cur_tok == None and self.cur_tok != T_EOS:
            return "needed", None

        if err := self.expect(T_EOS):
            return None, err

        end_idx = self.cur_pos
        self.next_tok() #consume EOS
        

        if (not var_expr) and (not var_type):
            return None, Exception(f"excepted a type or a default value, {var_name}")

        varDecNode = VarDeclareNode(var_name)

        if var_expr:
            varDecNode.expr = var_expr
        else:
            varDecNode.expr = ConstantNode(0, "int")

        if var_type:
            varDecNode.llvm_type = var_type

        #cutting the privious successful node
        self.tokens = cutOut(self.tokens, self.node_start, end_idx)
        #from current index to the end

        self.cur_pos = self.node_start

        return varDecNode, None


    def parse_assign(self, iden):
        self.next_tok()

        expression, err = self.compare_expr()

        if expression == "needed": return "needed", None
        if err: return None, err

        if err := self.expect(T_EOS):
            return None, ere

        end_idx = self.cur_pos
        self.next_tok() #consume EOS

        if iden in variables_ptr:

            #cutting the last successful node
            self.tokens = cutOut(self.tokens, self.node_start, end_idx)
            #from current position to end remains

            #fix the index pointer
            self.cur_pos = self.node_start

            return VarAssignNode(
                variables_ptr[iden]["value"],
                expression,
                variables_ptr[iden]["type"]
            ), None

        #else
        return None, Exception(f"unknow identifier {iden_name}")

    def parse_if(self):
        self.next_tok()

        if self.cur_tok == None:
            return "needed", None

        elif self.cur_tok == T_EOF:
            return None, Exception("expected condition after if")

        #adjusting the end point of expr
        pre_eoe = self.EOE
        self.EOE = T_COLON
        cond_expr, err = self.compare_expr()

        if cond_expr == "needed":
            return "needed", None

        if err: return None, err

        if isinstance(cond_expr, BinOpNode):
            return None, Exception("expected a comparision node but got arithmatic node")

        self.next_tok() #consume the colon
        self.EOE = pre_eoe #back to previous

        #check for need
        if self.cur_tok == None:
            return "needed", None

        elif self.cur_tok == T_EOF:
            return None, Exception("excepted at least end keyword to close the if block")

        if Token(T_KEY, "end") not in self.tokens: 
            return "needed", None

        stmts = []
        self_start_pos = self.node_start #preserving the pointer
        
        while self.cur_tok and self.cur_tok.value != "end":
            res, err = self.router()

            if res == "needed":
                return None, "something went wrong from if block"

            if err:
                return None, err

            stmts.append(res)

        end_idx = self.cur_pos
        self.next_tok() # consume the end key

        #cutting the last successful node
        self.tokens = cutOut(self.tokens, self_start_pos, end_idx)

        return IfThenBlock(cond_expr, stmts), None
        

    def router(self) -> tuple[Any, Exception]:

        #the variable declaration part
        if self.cur_tok.value == "let":
            self.node_start = self.cur_pos
            return self.parse_var()

        #if block entry point
        elif self.cur_tok.value == "if":
            self.node_start = self.cur_pos
            return self.parse_if()

        #calling or assign entry point
        elif self.cur_tok == T_IDEN:

            iden_name = self.cur_tok.value
            self.node_start = self.cur_pos
            self.next_tok()

            if self.cur_tok == None:
                return "needed", None

            elif self.cur_tok == T_EOF:
                return None, Exception(f"excepted more tokens after {iden_name}")

            #means this is a assign node
            if self.cur_tok == T_EQ:
                return self.parse_assign(iden_name)

            #this is a call node
            elif self.cur_tok == T_LPAN1:
                pass

        return "needed", None


    def parse(self) -> tuple[Any, Exception]:


        self.cur_pos = -1
        #one step before the original
        #because it will currect itself
        self.next_tok()

        if self.cur_tok == None:
            return "needed", None

        elif self.cur_tok == T_EOF:
            return "theend", None #end point

        
        return self.router()

    #end function

#end class

