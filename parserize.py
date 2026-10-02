from nodes import (
    Node,
    ConstantNode,
    CompareNode,
    BinOpNode,
    NegNode,
    PosNode,
    StringNode,
    VarFetchNode,
    VarAssignNode,
    VarDeclareNode,
    CallNode,
    IfElseBlock,
    DefaultBlock,
    ElseBlock,
)

from utils import (
    T_EOS,
    T_IDEN,
    T_EQ,
    T_EQS,
    T_NEQ,
    T_LT,
    T_LTE,
    T_GT,
    T_GTE,
    T_EOF,
    T_RPAN1,
    T_LPAN1,
    T_LITERAL,
    T_COLON,
    T_COMMA,
    T_ADD,
    T_SUB,
    T_MUL,
    T_DIV,
    T_MOD,
    Position,
)

from lexical import Token, Lexer

class Parser:

    def __init__(self):
        self.tokens:list[Token] = []
        self.cur_tok = None
        self.cur_pos = -1
        self.node_start = 0
        self.EOE = [T_EOS]
        self.cache: list[tuple[int, Node | DefaultBlock]] = []
        self.indent = 0
        self.lexer = Lexer()
        self.ctx = None
        self.file = None

    def start_up(self):
        self.cur_pos = -1
        self.cur_tok = None

        return self.next_tok()

    def consume(self) -> Exception | None:
        line = self.file.read()

        if line == "":
            tokens = [Token(T_EOF, Position(0,0))]

        else:
            tokens, err = self.lexer.lex(line)
            if err: return err

        for tok in tokens:
            self.tokens.append(tok)

        return None


    def set_context(self, ctx, file):
        self.ctx = ctx
        self.file = file


    def next_tok(self) -> tuple[bool, Exception | None]:
        self.cur_pos += 1

        if len(self.tokens) > self.cur_pos:
            self.cur_tok = self.tokens[self.cur_pos]
        else:
            # self.cur_tok = None
            if err := self.consume():
                return False, err

            self.cur_tok = self.tokens[self.cur_pos]

        if self.cur_tok == T_EOF:
            return True, None
        else: 
            return False, None
        

    def expr(self, min_bp = 0) -> tuple[Node | None, Exception | None]:

        left, err = self.factor()

        if left == "theend": return left, err
        if err: return None, err

        eof, err = self.next_tok()

        if eof: return "theend", Exception("@parser, excepted more tokens")
        if err: return None, err

        while self.cur_tok not in self.EOE:

            operand = self.cur_tok

            if operand == T_RPAN1:
                return left, None

            lbp, rbp, err = self.get_binding_power(operand)

            if lbp < min_bp:
                break

            eof, err = self.next_tok()

            if eof: return "theend", Exception("@parser, excepted more tokens")
            if err: return None, err

            right, err = self.expr(rbp)

            if err: return None, err

            if lbp in (5,7):
                left = BinOpNode(operand, left, right)
            elif lbp == 3:
                left = CompareNode(operand, left, right)

            # I have covered all the cases
            # there should not be another case left

        return left, None


    def factor(self) -> tuple[Node | None, Exception | None]:

        if self.cur_tok.type in (T_ADD, T_SUB):
            sign = True if self.cur_tok == T_ADD else False

            eof, err = self.next_tok()

            if eof: return "theend", Exception("@parser, excepted more tokens")
            if err: return None, err

            res, err = self.factor()
            if err: return None, err

            if sign: return PosNode(res), None
            return NegNode(res), None

        elif self.cur_tok.typer in ("int", "float"):
            return ConstantNode(
                self.cur_tok.value, 
                self.cur_tok.typer
            ), None

        elif self.cur_tok.typer == "string":
            return StringNode(self.cur_tok.value), None

        elif self.cur_tok == T_IDEN:
            return VarFetchNode(self.cur_tok.value), None

        elif self.cur_tok == T_LPAN1:

            eof, err = self.next_tok()

            if eof: return "theend", Exception("@parser, expected more tokens")
            if err: return None, err

            res, err = self.expr()
            
            if err: return None, err
            
            if self.cur_tok == T_RPAN1:
                return res, None
            return None, Exception("@parser, found no closing paranthisis!")

        return None, Exception(f"@parser, unknown prefix or operand {self.cur_tok}!")

    def get_binding_power(self, op) -> tuple[int, int, Exception | None]:

        if op.type in (T_ADD, T_SUB):
            return 5, 6, None

        elif op.type in (T_MUL, T_DIV, T_MOD):
            return 7, 8, None

        elif op.type in (
            T_EQ, T_EQS,
            T_LT, T_LTE,
            T_GT, T_GTE
        ): return 3, 4, None

        else: return 0, 0, Exception(f"@parser, invalid operand {op}")
        
        
    def expect(self, *v, isType = True) -> Exception | None:

        if isType:
            if not self.cur_tok.type in v:
                return Exception(f"@parser, expected {v} as type")
        else:
            if not self.cur_tok.value in v:
                return Exception(f"@parser, expected {v} as value")
        return None
        

    def parse_var(self) -> tuple[Node | None, Exception | None]:

        eof, err = self.next_tok()

        if eof:
            return "theend", Exception("@parser, expected more tokens")
        elif err:
            return None, err            

        if err := self.expect(T_IDEN):
            return None, err

        var_name = self.cur_tok.value
        var_type = 0
        var_expr = 0

        eof, err = self.next_tok()

        if eof:
            return "theend", Exception("@parser, expected more tokens")
        elif err:
            return None, err

        if self.cur_tok == T_COLON:
        
            eof, err = self.next_tok()

            if eof:
                return "theend", Exception("@parser, expected more tokens")
            elif err:
                return None, err

            if err := self.expect(
                "int", "char", "short", "bool", #integer types
                "float", "double", #floating point types
                "string", # fancy name for charptr
                isType=False
            ): return None, err

            var_type = self.cur_tok.value
            eof, err = self.next_tok()

            if eof:
                return "theend", Exception("@parser, expected more tokens")
            elif err: 
                return None, err

        if self.cur_tok == T_EQ:
            eof, err = self.next_tok()

            if eof:
                return "theend", Exception("@parser, expected more tokens")
            elif err:
                return None, err

            var_expr, err = self.expr()

            if var_expr == 'theend': return var_expr, err
            if err: return None, err

        if err := self.expect(T_EOS):
            return None, err


        end_idx = self.cur_pos
        eof, err = self.next_tok() #consume EOS

        if err:
            return None, err        

        if (not var_expr) and (not var_type):
            return None, Exception(f"@parser, excepted a type or a default value, {var_name}")

        varDecNode = VarDeclareNode(var_name)

        if var_expr:
            varDecNode.expr = var_expr
        else:
            varDecNode.expr = ConstantNode(0, "int")

        if var_type:
            varDecNode.llvm_type = var_type

        return varDecNode, None


    def parse_assign(self, iden):

        eof, err = self.next_tok()

        if eof:
            return "theend", Exception("@parser, expected more tokens")

        elif err:
            return None, err

        expression, err = self.expr()

        if expression == 'theend': return expression, err
        if err: return None, err

        if err := self.expect(T_EOS):
            return None, err

        end_idx = self.cur_pos
        eof, err = self.next_tok() #consume EOS
        if err:
            return None, err

        return VarAssignNode(iden, expression), None

    def parse_if(self):
    
        eof, err = self.next_tok()
        
        if eof:
            return "theend", Exception("@parser, expected condition after if")

        elif err:
            return None, err

        #adjusting the end point of expr
        pre_eoe = self.EOE
        self.EOE = [T_COLON]

        start_pos = self.node_start
        
        cond_expr, err = self.expr()

        if cond_expr == 'theend': return cond_expr, err
        if err: return None, err

        # adjusting the cond_expr
        if isinstance(cond_expr, (BinOpNode, ConstantNode, VarFetchNode)):
            cond_expr = CompareNode(
                T_GT,
                cond_expr,
                ConstantNode(0, "int")
            )

        eof, err = self.next_tok()
        
        if eof:
            return "theend" , Exception("@parser, excepted at least end keyword to close the if block")

        elif err:
            return None, err

        self.EOE = pre_eoe #back to previous

        while self.cur_tok.value not in (
            "end", "elif", "else"
        ):
            res, err = self.parse()

            if res == 'theend':
                return res, err
            elif err: 
                return None, err

            self.cache.append((self.indent, res))

        if self.cur_tok == T_EOF:
            return None, Exception("@parser, excepted at least \"end\" to close the if block")

        current_block = IfElseBlock(
            cond_expr,
            [x[1] for x in self.cache if x[0] == self.indent],
            DefaultBlock()
        )

        # clean up
        idx = 0
        while idx < len(self.cache):
            if self.cache[idx][0] == self.indent:
                self.cache.pop(idx)
                continue

            idx += 1
        
        #branch checking
        if self.cur_tok.value == "elif":
            self.node_start = self.cur_pos
            
            res, err = self.parse_if()
            if res == "theend": return res, err
            if err: return None, err

            # return with res
            current_block.else_block = res
            return current_block, None
            
        elif self.cur_tok.value == "else":
            self.node_start = self.cur_pos
            
            res, err = self.parse_else()
            if res == "theend": return res, None
            if err: return None, err

            #returning with res
            current_block.else_block = res
            return current_block, None

        # we expect an end key
        if err := self.expect('end', isType=False):
            return None, err
        
        end_idx = self.cur_pos
        eof, err = self.next_tok() # consume end

        if err:
            return None, err

        return current_block, None
    #end

    def parse_else(self):

        eof, err = self.next_tok() #consume else key

        if eof:
            return "theend", Exception("@parser, expected more tokens")
        elif err:
            return None, err

        if err := self.expect(T_COLON):
            return None, err

        eof, err = self.next_tok() # consume the colon

        if eof:
            return 'theend', Exception("@parser, expected more tokens")

        elif err:
            return None, err

        start_pos = self.node_start

        while self.cur_tok.value != "end":
            res, err = self.parse()

            if res == 'theend': 
                return res, Exception("@parser, excepted at least \"end\" to close the if block")

            elif err: 
                return None, err

            self.cache.append((self.indent, res))

        # we expect an end key
        if err := self.expect('end', isType=False):
            return None, err

        current_block = ElseBlock(
            [x[1] for x in self.cache if x[0] == self.indent]
        )

        # clean up
        idx = 0
        while idx < len(self.cache):
            if self.cache[idx][0] == self.indent:
                self.cache.pop(idx)
                continue

            idx += 1

        end_pos = self.cur_pos
        eof, err = self.next_tok() # consume the end key

        if err:
            return None, err

        return current_block, None

    def parse_call(self, iden):

        err_msg = ("@parser, expected more tokens to "+
        "complete the call parsing")

        eof, err = self.next_tok()
        if eof: return "theend", Exception(err_msg)
        if err: return None, err

        # preserve the eoe and assign new one
        pre_eoe = self.EOE
        self.EOE = [T_RPAN1, T_COMMA]

        params = []
        if self.cur_tok != T_RPAN1:

            while True:
                # error check for looping
                if self.cur_tok == T_RPAN1:
                    return None, Exception(
                        "@parsar, we expect one more expression "
                        "after comma but you have forgotten "
                        "to put an expression after comma "
                        "inside a function call"
                    )
                    
                res, err = self.expr()
                if res == "theend": return res, err
                if err: return None, err

                params.append(res)

                if self.cur_tok == T_RPAN1:
                    break

                if self.cur_tok == T_COMMA:
                    eof, err = self.next_tok()
                    if eof: return "theend", Exception(err_msg)
                    if err: return None, err

            eof, err = self.next_tok()
            if eof: return "theend", Exception("expected at least one semicolon")

        if err := self.expect(T_EOS):
            return None, err

        # consume the eos
        eof, err = self.next_tok()
        if err: return None, err

        #restoring eoe
        self.EOE = pre_eoe
        
        return CallNode(iden, params), None


    def parse(self) -> tuple[ DefaultBlock | Node | None, Exception | None]:

        if self.cur_tok == T_EOF:
            return "theend", None
        
        #the variable declaration part
        if self.cur_tok.value == "let":
            self.node_start = self.cur_pos
            return self.parse_var()

        #if block entry point
        elif self.cur_tok.value == "if":
        
            self.node_start = self.cur_pos
            self.indent += 1
            
            res = self.parse_if()
            self.indent -= 1

            return res

        #calling or assign entry point
        elif self.cur_tok == T_IDEN:

            iden_name = self.cur_tok.value
            self.node_start = self.cur_pos
            eof, err = self.next_tok()

            if eof:
                return "theend", Exception(f"@parser, excepted more tokens after {iden_name}")
            elif err:
                return None, err

            #means this is an assign node
            if self.cur_tok == T_EQ:
                return self.parse_assign(iden_name)

            #means this is a calling node
            if self.cur_tok == T_LPAN1:
                return self.parse_call(iden_name)

        return self.expr()

    #end function

#end class

