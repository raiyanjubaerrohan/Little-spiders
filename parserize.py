from nodes import (
    Node,
    ConstantNode,
    BitNode,
    CompareNode,
    BinOpNode,
    NegNode,
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
        if err: return None, Exception("@parser, excepted more tokens")

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
            if right == "theend": return right, err
            if err: return None, err

            if lbp in (5,7):
                left = BinOpNode(operand, left, right)
            elif lbp == 3:
                left = CompareNode(operand, left, right)

            # I have covered all the cases
            # there should not be another case left

        return left, None


    def factor(self) -> tuple[Node | None, Exception | None]:

        layers = []

        while True:
            if self.cur_tok.type in (T_ADD, T_SUB):
                nosign = self.cur_tok == T_SUB

                eof, err = self.next_tok()
                if eof: return "theend", Exception("@parser, excepted more tokens")
                if err: return None, err

                if nosign: layers.append(NegNode)
                # there is not need for PosNode,
                # it is not required

                eof, err = self.next_tok()
                if eof: return "theend", Exception("@parser, excpted more tokens")
                if err: return None, err

            elif self.cur_tok.typer in ("int", "float"):
                layers.append(ConstantNode(
                    self.cur_tok.value,
                    self.cur_tok.typer
                ))

                eof, err = self.next_tok()
                if eof: return "theend", Exception("@parser, excpted more tokens")
                if err: return None, err
                # a leaf node so breaking the loop
                break

            elif self.cur_tok.typer == "char":
                layers.append(ConstantNode(
                    ord(self.cur_tok.value),
                    self.cur_tok.typer
                ))

                eof, err = self.next_tok()
                if eof: return "theend", Exception("@parser, expected more tokens")
                if err: return None, err

                # leaf node, so breaking the loop
                break

            elif self.cur_tok.typer == "string":
                layers.append(StringNode(self.cur_tok.value))

                eof, err = self.next_tok()
                if eof: return "theend", Exception("@parser, expected more tokens")
                if err: return None, err

                # a leaf node so breaking the loop
                break

            elif self.cur_tok.typer == "bool":
                layers.append(BitNode(self.cur_tok.value))
                # a leaf node, so breaking the loop

                eof, err = self.next_tok()
                if eof: return "theend", Exception("@parser, expected more tokens")
                if err: return None, err

                break

            elif self.cur_tok == T_IDEN:
                iden = self.cur_tok.value

                eof, err = self.next_tok()
                if eof: return "theend", Exception("@parser, expected more tokens")
                if err: return None, err

                if self.cur_tok == T_LPAN1:
                    res, err = self.parse_call(iden)
                    if err: return None, err

                    layers.append(res)

                else:
                    layers.append(VarFetchNode(iden))
                # a leaf node, so breaking the loop
                break

            elif self.cur_tok == T_LPAN1:

                eof, err = self.next_tok()
                if eof: return "theend", Exception("@parser, expected more tokens")
                if err: return None, err

                # we have no choice
                res, err = self.expr()
                if res == "theend": return res, err
                if err: return None, err

                if self.cur_tok == T_RPAN1:
                    layers.append(res)
                    break

                return None, Exception("@parser, found no closing paranthisis!")

            else:
                return None, Exception(f"@parser, unknown prefix or operand {self.cur_tok}!")

        # now, rebuilding the tree

        idx = len(layers) - 1 # the last index
        result = layers[idx] # the last one, the result
        idx -= 1

        while idx >= 0:
            result = layers[idx](result) #wrap itself
            idx -= 1

        return result, None

    def get_binding_power(self, op) -> tuple[int, int, Exception | None]:

        if op.type in (T_ADD, T_SUB):
            return 5, 6, None

        if op.type in (T_MUL, T_DIV, T_MOD):
            return 7, 8, None

        if op.type in (
            T_NEQ, T_EQS,
            T_LT, T_LTE,
            T_GT, T_GTE
        ): return 3, 4, None

        return 0, 0, Exception(f"@parser, invalid operand {op}")

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
        if eof: return "theend", Exception("@parser, expected more tokens")
        elif err: return None, err

        if err := self.expect(T_IDEN):
            return None, err

        var_name = self.cur_tok.value
        var_type = 0
        var_expr = 0

        eof, err = self.next_tok()
        if eof: return "theend", Exception("@parser, expected more tokens")
        if err: return None, err

        if self.cur_tok == T_COLON:

            eof, err = self.next_tok()
            if eof: return "theend", Exception("@parser, expected more tokens")
            elif err: return None, err

            if err := self.expect(
                "int", "char", "short", "bool", #integer types
                "float", "double", #floating point types
                "string", # fancy name for charptr
                isType=False
            ): return None, err

            var_type = self.cur_tok.value
            eof, err = self.next_tok()
            if eof: return "theend", Exception("@parser, expected more tokens")
            if err: return None, err

        if self.cur_tok == T_EQ:
            eof, err = self.next_tok()
            if eof: return "theend", Exception("@parser, expected more tokens")
            if err: return None, err

            var_expr, err = self.expr()
            if var_expr == 'theend': return var_expr, err
            if err: return None, err

        if err := self.expect(T_EOS):
            return None, err

        eof, err = self.next_tok() #consume EOS
        if err: return None, err

        if (not var_expr) and (not var_type):
            return None, Exception(f"@parser, excepted a type or a default value, {var_name}")

        varDecNode = VarDeclareNode(var_name)

        if var_expr: varDecNode.expr = var_expr
        else: varDecNode.expr = ConstantNode(0, "int")

        if var_type: varDecNode.llvm_type = var_type

        return varDecNode, None


    def parse_assign(self, iden):

        eof, err = self.next_tok()
        if eof: return "theend", Exception("@parser, expected more tokens")
        if err: return None, err

        expression, err = self.expr()
        if expression == 'theend': return "theend", err
        if err: return None, err

        if err := self.expect(T_EOS):
            return None, err

        eof, err = self.next_tok() #consume EOS
        if err: return None, err

        return VarAssignNode(iden, expression), None

    def parse_if(self) -> tuple[
        IfElseBlock | None,
        Exception | None
    ]:

        eof, err = self.next_tok()
        if eof: return "theend", Exception("@parser, expected condition after if")
        if err: return None, err

        #adjusting the end point of expr
        pre_eoe = self.EOE
        self.EOE = [T_LPAN2]

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

        self.EOE = pre_eoe #back to previous

        nodes, err = self.parse_block()
        if nodes == "theend": return nodes, err
        if err: return None, err

        current_block = IfElseBlock(
            cond_expr,
            nodes,
            DefaultBlock()
        )

        #branch checking
        if self.cur_tok.value == "elif":
            self.node_start = self.cur_pos

            res, err = self.parse_if()
            if res == "theend": return res, err
            if err: return None, err

            # return with res
            current_block.else_block = res
            return current_block, None

        if self.cur_tok.value == "else":
            self.node_start = self.cur_pos

            res, err = self.parse_else()
            if res == "theend": return res, None
            if err: return None, err

            #returning with res
            current_block.else_block = res
            return current_block, None

        return current_block, None
    #end

    def parse_else(self) -> tuple[
        ElseBlock | None,
        Exception | None
    ]:

        eof, err = self.next_tok() #consume else key
        if eof: return "theend", Exception("@parser, expected more tokens")
        if err: return None, err

        nodes, err = self.parse_block()
        if nodes == "theend": return nodes, err
        if err: return None, err

        current_block = ElseBlock(nodes)

        return current_block, None

    def parse_while(self) -> tuple[
        WhileBlock | None,
        Exception  | None
    ]:

        # remove the while
        eof, err = self.next_tok()
        if eof: return "theend", Exception(f"@parser, expected condition after while keyword")
        if err: return None, err

        # parse the condition
        pre_eoe = self.EOE
        self.EOE = [T_LPAN2]

        cond_expr, err = self.expr()
        if cond_expr == "theend": return cond_expr, err
        if err: return None, err

        # adjust the condition node
        if isinstance(cond_expr, (BinOpNode, ConstantNode, VarFetchNode)):
            cond_expr = CompareNode(
                T_GT,
                cond_expr,
                ConstantNode(0, "int")
            )

        self.EOE = pre_eoe # restoring

        nodes, err = self.parse_block()
        if nodes == "theend": return nodes, err
        if err: return None, err

        # for now I am skipping the fallback part

        return WhileBlock(cond_expr, nodes, DefaultBlock()), None

    def parse_call(self, iden) -> tuple[
        CallNode  | None,
        Exception | None
    ]:

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
            if eof: return "theend", Exception("@parser, expected at least one semicolon")
            if err: return None, err

        #restoring eoe
        self.EOE = pre_eoe

        return CallNode(iden, params), None

    def parse_block(self) -> tuple[
        list[Node | DefaultBlock] | None,
        Exception | None]:

        if err := self.expect(T_LPAN2):
            return None, err

        eof, err = self.next_tok()
        if eof: return "theend", Exception("@parser, expected a '}' to close the block")
        if err: return None, err

        nodes = []
        while self.cur_tok != T_RPAN2:
            res, err = self.parse()
            if res == "theend": return "theend", Exception(
                "@parser, you have forget to put "
                "a '}'. So, we can not parse it."
            )
            if err: return None, err

            nodes.append(res)

        eof, err = self.next_tok()
        if err: return None, err

        return nodes, None

    def parse(self) -> tuple[ DefaultBlock | Node | None, Exception | None]:

        if self.cur_tok == T_EOF:
            return "theend", None

        #the variable declaration part
        if self.cur_tok.value == "let":
            return self.parse_var()

        #if block entry point
        elif self.cur_tok.value == "if":
            return self.parse_if()

        elif self.cur_tok.value == "while":
            return self.parse_while()

        elif self.cur_tok.value == "continue":

            if err := self.expect(T_EOS, isType=True):
                return None, err
            
            eof, err = self.next_tok()
            if eof: return "theend", Exception("@parser, expected more tokens")
            if err: return None, err

            return ConstantNode(), None

        elif self.cur_tok.value == "break":

            if err := self.expect(T_EOS, isType=True):
                return None, err

            eof, err = self.next_tok()
            if eof: return "theend", Exception("@parser, expected more tokens")
            if err: return None, err

            return BreakNode(), None

        #calling or assign entry point
        elif self.cur_tok == T_IDEN:

            iden_name = self.cur_tok.value

            eof, err = self.next_tok()
            if eof: return "theend", Exception(f"@parser, excepted more tokens after {iden_name}")
            elif err: return None, err

            #means this is an assign node
            if self.cur_tok == T_EQ:
                return self.parse_assign(iden_name)

            #means this is a calling node
            if self.cur_tok == T_LPAN1:
                res, err = self.parse_call(iden_name)

                if err := self.expect(T_EOS, isType=True):
                    return None, err

                eof, err = self.next_tok()
                if err: return None, err

                return res, None

        return self.expr()

    #end function
#end class

