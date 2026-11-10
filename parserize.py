from nodes import (
    Node,
    ConstantNode,
    BitNode,
    BitOpNode,
    CompareNode,
    BinOpNode,
    NegNode,
    NotNode,
    StringNode,
    VarFetchNode,
    VarAssignNode,
    VarDeclareNode,
    CallNode,
    BreakNode,
    ContinueNode,
    IfElseBlock,
    DefaultBlock,
    ElseBlock,
    WhileBlock,
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
    T_RPAN2,
    T_LPAN2,
    T_COLON,
    T_COMMA,
    T_ADD,
    T_SUB,
    T_MUL,
    T_DIV,
    T_MOD,
    T_POISON,
)

from diagnostical import Diagnostics

class Parser:

    def __init__(self, diagctx):
        self.tokens:list[Token] = []
        self.cur_tok = None
        self.cur_pos = 0
        self.EOE = [T_EOS]
        self.cache: list[tuple[int, Node | DefaultBlock]] = []
        self.indent = 0
        self.diagctx = diagctx
        self.start_pos = None

    def load(self, tokens):
        self.tokens = tokens
        self.cur_pos = -1
        self.cur_tok = None

        return self.next_tok()

    def next_tok(self) -> bool:
        self.cur_pos += 1
        self.cur_tok = self.tokens[self.cur_pos] if len(self.tokens) > self.cur_pos else T_EOF

        return self.cur_tok == T_EOF

    def expr(self, min_bp = 0) -> Node | None:

        left = self.factor()
        if not left or left == T_POISON: return
        if left == "theend": return left

        while self.cur_tok not in self.EOE:

            operand = self.cur_tok
            if operand == T_RPAN1:
                return left

            lbp, rbp = self.get_binding_power(operand)

            if lbp < min_bp:
                break

            if eof := self.next_tok():
                self.diagctx.emit(Diagnostics(
                    "the parser is expecting more tokens to build a tree",
                    "P0337",
                    left.span + operand.pos
                ))
                return "theend"

            right = self.expr(rbp)
            if not right or right == T_POISON: return
            if right == "theend": return right

            if lbp in (7,9):
                left = BinOpNode(operand, left, right, left.span+right.span)
            elif lbp == 5:
                left = CompareNode(operand, left, right, left.span+right.span)
            elif lbp == 3:
                left = BitOpNode(operand.value, left, right, left.span+right.span)
            else:
                self.diagctx.emit(Diagnostics(
                    "internal error: no operand type matched the list",
                    "E0489",
                    operand.pos
                ))
                return

            # I have covered all the cases
            # there should not be another case left
        return left

    def factor(self) -> Node | str:

        layers: list[tuple[Node, int | Span]] = []
        pre_start_pos = self.start_pos

        while True:
            self.start_pos = self.cur_tok.pos
            
            if self.cur_tok.type in (T_ADD, T_SUB):

                if self.cur_tok == T_SUB: layers.append((NegNode, self.start_pos))
                # there is not need for PosNode,
                # it is not required

                if eof := self.next_tok():
                    self.diagctx.emit(Diagnostics(
                        "the parser is expecting more tokens to build a tree",
                        "P0337",
                        self.start_pos
                    ))
                    return "theend"

            elif self.cur_tok.value == "not":

                layers.append((NotNode, self.start_pos))

                if eof := self.next_tok():
                    self.diagctx.emit(Diagnostics(
                        "the parser is expecting more tokens to build a tree",
                        "P0337",
                        self.start_pos
                    ))
                    return "theend"

            elif self.cur_tok.typer in ("int", "float", "char", "string", "bool"):
                res = self.parse_literals()
                if res == "theend": return res

                layers.append((res, 0))
                break

            elif self.cur_tok == T_IDEN:
                iden = self.cur_tok

                if eof := self.next_tok():
                    self.diagctx.emit(Diagnostics(
                        "the parser is expecting more tokens to build a tree",
                        "P0337",
                        iden.pos
                    ))
                    return "theend"

                if self.cur_tok == T_LPAN1:
                    layers.append((self.parse_call(iden.value), 0))
                else:
                    layers.append((VarFetchNode(iden.value, iden.pos), 0))

                # a leaf node, so breaking the loop
                break

            elif self.cur_tok == T_LPAN1:

                if eof := self.next_tok():
                    self.diagctx.emit(Diagnostics(
                        "the parser is expecting more tokens to build a tree",
                        "P0337",
                        self.start_pos
                    ))
                    return "theend"

                # we have no choice
                res = self.expr()
                if res == "theend": return res

                if self.cur_tok == T_RPAN1:
                    end_pos = self.cur_tok.pos

                    if eof := self.next_tok():
                        self.diagctx.emit(Diagnostics(
                            "Expected at least a semicolon to end the expression",
                            "P0334",
                            self.start_pos + end_pos
                        ))
                        return "theend"

                    layers.append((res, 0))
                    break

                else:
                    self.diagctx.emit(Diagnostics(
                        "found no closing paranthisis!",
                        "P0459",
                        start_pos + self.cur_tok.pos
                    ))
                    return
            else:
                self.diagctx.emit(Diagnostics(
                    f"unknown prefix or operand {self.cur_tok}!",
                    "P0503",
                    self.cur_tok.pos
                ))
                return

        # now, rebuilding the tree

        idx = len(layers) - 1 # the last index
        result = layers[idx][0] # the last one, the result
        idx -= 1

        while idx >= 0:
            result = layers[idx][0](result, layers[idx][1] + result.span) #wrap itself
            idx -= 1

        # restoring
        self.start_pos = pre_start_pos

        return result

    def parse_literals(self) -> Node | str | None:
        # this function is forbidden to call self.factor or self.expr

        result = None
    
        if self.cur_tok.typer in ("int", "float"):
            result = ConstantNode(
                self.cur_tok.value,
                self.cur_tok.pos,
                self.cur_tok.typer
            )

        elif self.cur_tok.typer == "char":
            result = ConstantNode(
                ord(self.cur_tok.value),
                self.cur_tok.pos,
                self.cur_tok.typer
            )

        elif self.cur_tok.typer == "string":
            result = StringNode(self.cur_tok.value, self.cur_tok.pos)

        elif self.cur_tok.typer == "bool":
            result = BitNode(self.cur_tok.value, self.cur_tok.pos)

        # there is no else because the call path is already fitered

        if eof := self.next_tok():
            self.diagctx.emit(Diagnostics(
                "the parser is expecting more tokens to build a tree",
                "P0337",
                self.start_pos + result.span
            ))

        return result
        
    def get_binding_power(self, op) -> tuple[int, int]:

        if op.type in (T_ADD, T_SUB):
            return 7, 8

        if op.type in (T_MUL, T_DIV, T_MOD):
            return 9, 10

        if op.value in ("and", "or"):
            return 3, 4

        if op.type in (
            T_NEQ, T_EQS,
            T_LT, T_LTE,
            T_GT, T_GTE
        ): return 5, 6

        self.diagctx.emit(Diagnostics(
            f"invalid operand {op}",
            "P0568",
            op.pos,
            smsg="repleca this with a better one"
        ))

        return 0, 0

    def expect(self, *v, isType = True) -> Diagnostics | None:

        if isType:
            if not self.cur_tok.type in v:
                return Diagnostics(
                    f"expected the type of {self.cur_tok} as one of this: {list(v)}, but got {self.cur_tok.type}",
                    "P0207",
                    self.cur_tok.pos,
                    smsg= f"replace it with one of this {list(v)} types"
                )
        else:
            if not self.cur_tok.value in v:
                return Diagnostics(
                    f"expected the value of {self.cur_tok} as one of this: {list(v)}, but got {self.cur_tok.value}",
                    "P0208",
                    self.cur_tok.pos,
                    smsg= f"replace it with one of this {list(v)} values"
                )

        return None

    def parse_var(self) -> VarDeclareNode | str:

        if eof := self.next_tok():
            self.diagctx.emit(Diagnostics(
                "the parser is expecting more tokens to build a tree",
                "P0337",
                self.start_pos
            ))
            return "theend"

        if err := self.expect(T_IDEN):
            self.diagctx.emit(err)
            return T_POISON

        var_name = self.cur_tok
        var_type = 0
        var_expr = 0

        if eof := self.next_tok():
            self.diagctx.emit(Diagnostics(
                "the parser is excepting more tokens to build a tree",
                "P0337",
                self.start_pos + var_name.pos
            ))
            return "theend"

        if self.cur_tok == T_COLON:
            last_pos = self.cur_tok.pos

            if eof := self.next_tok():
                self.diagctx.emit(Diagnostics(
                    "the parser is excepting more tokens to build a tree",
                    "P0337",
                    self.start_pos + last_pos
                ))

            if err := self.expect(
                "int", "char", "short", "bool", #integer types
                "float", "double", #floating point types
                "string", # fancy name for charptr
                isType=False
            ):
                self.diagctx.emit(err)
                return T_POISON

            var_type = self.cur_tok
            
            if eof := self.next_tok():
                self.diagctx.emit(Diagnostics(
                    "the parser is excepting more tokens to build a tree",
                    "P0337",
                    self.start_pos + var_type.pos
                ))

        if self.cur_tok == T_EQ:
            last_pos = self.cur_tok.pos
            if eof := self.next_tok():
                self.diagctx.emit(Diagnostics(
                    "the parser is excepting more tokens to build a tree",
                    "P0337",
                    self.start_pos + last_pos
                ))

            var_expr = self.expr()
            if not var_expr: return T_POISON
            if var_expr == 'theend': return var_expr

        if err := self.expect(T_EOS):
            self.diagctx.emit(err)
            return T_POISON

        last_pos = self.cur_tok.pos

        _ = self.next_tok() #consume EOS

        if (not var_expr) and (not var_type):
            self.diagctx.emit(Diagnostics(
                "expected a expression or a type hint to guess the type, but none are given",
                "P0910",
                var_name.pos,
                _help="add a colon then a type or a equal sign then a expression"
            ))
            return T_POISON

        varDecNode = VarDeclareNode(
            var_name.value,
            self.start_pos + last_pos,
            var_type.value if var_type else 0,
            var_expr if var_expr else ConstantNode(0, "int")
        )

        return varDecNode

    def parse_assign(self, iden) -> VarAssignNode | str:

        if eof := self.next_tok():
            self.diagctx.emit(Diagnostics(
                "the parser is excepting more tokens to build a tree",
                "P0337",
                iden.pos
            ))
            return "theend"

        expression = self.expr()
        if not expression: return T_POISON
        if expression == 'theend': return "theend"

        if err := self.expect(T_EOS):
            self.diagctx.emit(err)
            return T_POISON

        _ = self.next_tok() #consume EOS

        return VarAssignNode(iden, expression, self.start_pos + self.cur_tok.pos)

    def parse_if(self) -> IfElseBlock | str:

        if eof := self.next_tok():
            self.diagctx.emit(Diagnostics(
                "the parser is expecting a condition after if keyword",
                "P0482",
                self.start_pos
            ))
            return "theend"

        #adjusting the end point of expr
        pre_eoe = self.EOE
        self.EOE = [T_LPAN2]

        cond_expr = self.expr()
        if not cond_expr: cond_expr = T_POISON
        elif cond_expr == 'theend': return cond_expr

        # adjusting the cond_expr
        if isinstance(cond_expr, (BinOpNode, BitOpNode, ConstantNode, VarFetchNode)):
            cond_expr = CompareNode(
                T_GT,
                cond_expr,
                ConstantNode(0, Span((0,0), (1,1)), "int"),
                cond_expr.span
            )

        self.EOE = pre_eoe #back to previous

        pre_start_pos = self.start_pos
        self.start_pos = self.cur_tok.pos

        nodes = self.parse_block()
        if nodes == "theend": return nodes

        self.start_pos = pre_start_pos

        current_block = IfElseBlock(
            cond_expr,
            nodes,
            DefaultBlock(),
            self.start_pos + self.cur_tok.pos
        )

        #branch checking
        if self.cur_tok.value == "elif":
            res = self.parse_if()

        elif self.cur_tok.value == "else":
            res = self.parse_else()

        else: return current_block

        if res == "theend": return res

        #returning with res
        current_block.else_block = res
        current_block.span += res.span

        return current_block

    def parse_else(self) -> ElseBlock | str:

        if eof := self.next_tok(): #consume else key
            self.diagctx.emit(Diagnostics(
                "the parser is excepting more tokens to build a tree",
                "P0337",
                self.start_pos
            ))
            return "theend"

        pre_start_pos = self.start_pos
        self.start_pos = self.cur_tok.pos
        
        nodes = self.parse_block()
        if nodes == "theend": return nodes

        self.start_pos = pre_start_pos

        return ElseBlock(nodes, self.start_pos + self.cur_tok.pos)

    def parse_while(self) -> WhileBlock | str:

        # consume the while
        if eof := self.next_tok():
            self.diagctx.emit(Diagnostics(
                "the parser is expecting a condition after while keyword",
                "P0482",
                self.start_pos
            ))
            return "theend"

        # parse the condition
        pre_eoe = self.EOE
        self.EOE = [T_LPAN2]

        cond_expr = self.expr()
        if not cond_expr: cond_expr = T_POISON
        if cond_expr == "theend": return cond_expr

        # adjust the condition node
        if isinstance(cond_expr, (BinOpNode, ConstantNode, VarFetchNode)):
            cond_expr = CompareNode(
                T_GT,
                cond_expr,
                ConstantNode(0, Span((0,0), (1,1)), "int"),
                cond_expr.span
            )

        self.EOE = pre_eoe # restoring
        pre_start_pos = self.start_pos
        self.start_pos = self.cur_tok.pos

        nodes = self.parse_block()
        if nodes == "theend": return nodes

        # restore
        self.start_pos = pre_start_pos

        wb = WhileBlock(
            cond_expr,
            nodes,
            DefaultBlock(),
            self.start_pos + self.cur_tok.pos
        )

        # brance checking
        if self.cur_tok.value == "elif":
            res = self.parse_if()

        elif self.cur_tok.value == "else":
            res = self.parse_else()

        else: return wb

        if res == "theend": return res

        wb.else_block = res
        wb.span += res.span
        
        return wb

    def parse_call(self, iden) -> CallNode | str:

        err_msg = ("the parser is expecting more tokens to "+
            "complete parsing the call expr")

        if eof := self.next_tok():
            self.diagctx.emit(Diagnostics(
                err_msg,
                "P0749",
                self.start_pos
            ))
            return "theend"

        # preserve the eoe and assign new one
        pre_eoe = self.EOE
        self.EOE = [T_RPAN1, T_COMMA]

        params = []
        if self.cur_tok != T_RPAN1:

            while True:
                # error check for looping
                if self.cur_tok == T_RPAN1:
                    self.diagctx.emit(Diagnostics(
                        "we expect one more expression "
                        "after comma but you have forgotten "
                        "to put an expression after comma "
                        "inside a function call",
                        "P0726",
                        self.start_pos + self.cur_tok.pos
                    ))

                res = self.expr()
                if not res: res = T_POISON
                elif res == "theend": return res

                params.append(res)

                if self.cur_tok == T_RPAN1:
                    break

                if self.cur_tok == T_COMMA:
                    last_pos = self.cur_tok.pos
                    
                    if eof := self.next_tok():
                        self.diagctx.emit(Diagnostics(
                            "we expected an expression after comma "
                            "then a closing parenthisis",
                            "P0159",
                            self.start_pos + last_pos
                        ))
                # else
            #end while
        if err := self.expect(T_RPAN1, isType=True):
            self.diagctx.emit(err)
            return T_POISON

        last_pos = self.cur_tok.pos

        # restoring eoe
        self.EOE = pre_eoe

        if eof := self.next_tok():
            self.diagctx.emit(Diagnostics(
                "we expected at least a closing parentthisis to end this expression",
                "P0356",
                self.start_pos + last_pos
            ))
            return T_POISON

        return CallNode(iden, params, self.start_pos + self.cur_tok.pos)

    def parse_block(self) -> list[Node | DefaultBlock] | str:

        if err := self.expect(T_LPAN2):
            self.diagctx.emit(Diagnostics(
                "we expect a { at the beginning of a block",
                "P0935",
                self.cur_tok.pos
            ))
            return T_POISON

        last_pos = self.cur_tok.pos
        
        if eof := self.next_tok():
            self.diagctx.emit(Diagnostics(
                "we expect a } at the end of a block but none were given",
                "P0935",
                self.start_pos + last_pos
            ))

        nodes = []
        pre_start_pos = self.start_pos
        
        while self.cur_tok != T_RPAN2:
        
            res = self.parse()
            if res == "theend":
                self.diagctx.emit(Diagnostics(
                    "you must have foeget to put a } at the end of a block",
                    "P0935",
                    pre_start_pos + self.tokens[self.cur_pos-1].pos
                ))
                return "theend"

            nodes.append(res)

        self.start_pos = pre_start_pos

        if eof := self.next_tok():
            return "theend"

        return nodes

    def expect_eos(self, node):

        if eof := self.next_tok():
            self.diagctx.emit(Diagnostics(
                "we expected at least one semicolon to continue",
                "P0395",
                self.start_pos
            ))

        if err := self.expect(T_EOS, isType=True):
            self.diagctx.emit(err)
            return T_POISON

        if eof := self.next_tok():
            self.diagctx.emit(Diagnostics(
                "we expect more tokens to continue parsing",
                "P0337",
                self.start_pos
            ))

        return node

    def parse(self) -> tuple[ DefaultBlock | Node | None, Exception | None]:

        if self.cur_tok == T_EOF: return "theend"

        self.start_pos = self.cur_tok.pos

        #the variable declaration part
        if self.cur_tok.value == "let":
            return self.parse_var()

        #if block entry point
        elif self.cur_tok.value == "if":
            return self.parse_if()

        elif self.cur_tok.value == "while":
            return self.parse_while()

        elif self.cur_tok.value == "continue":
            return self.expect_eos(ContinueNode())

        elif self.cur_tok.value == "break":
            return self.expect_eos(BreakNode())

        #calling or assign entry point
        elif self.cur_tok == T_IDEN:

            iden_name = self.cur_tok

            if eof := self.next_tok():
                self.diagctx.emit(Diagnostics(
                    "we expect a equal sign '=' or a prenthisis after an identifier "
                    "at the start of a instruction",
                    "P0537",
                    iden_name.pos
                ))
                return T_POISON

            #means this is an assign node
            if self.cur_tok == T_EQ:
                return self.parse_assign(iden_name.value)

            #means this is a calling node
            if self.cur_tok == T_LPAN1:
                res = self.parse_call(iden_name.value)

                if err := self.expect(T_EOS, isType=True):
                    self.diagctx.emit(err)
                    return T_POISON

                if eof := self.next_tok():
                    return "theend"

                return res

        return self.expr()

    #end function
#end class

