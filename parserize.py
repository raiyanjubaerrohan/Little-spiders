from nodes import *
from utils import T_EOS, variables_ptr, T_IDEN, T_EQ
from utils import T_EQS, T_NEQ, T_LT, T_LTE, T_GT, T_GTE
from lexical import Token

class Parser:

    def __init__(self):
        self.tokens:list[Token] = []
        self.cur_tok = None
        self.cur_pos = 0
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
        self.tokens = self.tokens[self.cur_pos:]
        #from current index to the end

        return varDecNode, None


    def parse_assign(self, iden):
        self.next_tok()

        expression, err = self.compare_expr()

        if expression == "needed": return "needed", None
        if err: return None, err

        if err := self.expect(T_EOS):
            return None, ere

        self.next_tok() #consume EOS

        if iden in variables_ptr:

            #cutting the last successful node
            self.tokens = self.tokens[self.cur_pos:]
            #from current position to end remains

            return VarAssignNode(
                variables_ptr[iden]["value"],
                expression,
                variables_ptr[iden]["type"]
            ), None

        #else
        return None, Exception(f"unknow identifier {iden_name}")


    def parse(self):


        self.cur_pos = -1
        #one step before the original
        #because it will currect itself
        self.next_tok()

        if self.cur_tok == None:
            return "needed", None

        elif self.cur_tok == T_EOF:
            return "theend", None #end point

        #variable declare entry point
        elif self.cur_tok.value == "let":
            return self.parse_var()

        #calling or assign entry point
        elif self.cur_tok == T_IDEN:

            iden_name = self.cur_tok.value
            self.next_tok()

            #means this is an assign node
            if self.cur_tok == T_EQ:
                return self.parse_assign(iden_name)

            #means this is a call node
            elif self.cur_tok == T_LPAN1:
                pass


        return "needed", None

    #end function

#end class

