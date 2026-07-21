from nodes import *
from lexical import *
from utils import T_EOS, T_IDEN, T_EQ, cutOut
from utils import T_EQS, T_NEQ, T_LT, T_LTE, T_GT, T_GTE
from utils import T_KEY, Position
from lexical import Token
from typing import Any

class Parser:

    def __init__(self):
        self.tokens:list[Token] = []
        self.cur_tok = None
        self.cur_pos = 0
        self.node_start = 0
        self.EOE = T_EOS
        self.cache: list[tuple[int, Node | MyBlock]] = []
        self.indent = 0
        self.lexer = Lexer()
        self.ctx = None
        self.file = None
        self.have_read = False


    def append(self, tok) -> Exception | None:
        self.tokens.append(tok)

    
    def consume(self) -> Exception | None:

        if self.have_read: return None

        line = self.file.read()

        tokens, err = self.lexer.lex(line)
        if err: return err

        tokens.append(Token(T_EOF, Position(0,0)))
        
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
        

    def compare_expr(self) -> tuple[Node | None, Exception | None]:
        left, err = self.expr()

        if left == "theend": return left, err
        if err: return None, err

        while (self.cur_tok != self.EOE
        and self.cur_tok.type in (
            T_EQS, T_NEQ, T_LT, T_LTE, T_GT, T_GTE
        )):

            if self.cur_tok == T_RPAN1:

                eof, err = self.next_tok()
                if eof:
                    return "theend", Exception("expected more tokens")
                elif err:
                    return None, err
                
                return left, None

            center = self.cur_tok.type
            eof, err = self.next_tok()

            if eof:
                return "theend", Exception("expected more tokens")
            elif err:
                return None, err

            right, err = self.expr()

            if right == 'theend': return right, err
            if err: return None, err
            left = CompareNode(center, left, right)

        return left, None


    def expr(self) -> tuple[Node | None, Exception | None]:

        left, err = self.term()

        if left == 'theend': return left, err
        if err: return None, err

        while (self.cur_tok != self.EOE
        and self.cur_tok.type in (
            T_ADD, T_SUB, T_MOD, T_RPAN1
        )):

            if self.cur_tok == T_RPAN1:
                eof, err = self.next_tok()

                if eof:
                    return "theend", Exception("expected more tokens")
                elif err:
                    return None, err
                    
                return left, None


            center = self.cur_tok.type

            eof, err = self.next_tok()
            if eof:
                return "theend", Exception("expected more tokens")
            elif err:
                return None, err

            right, err = self.term()

            if right == "theend": return right, err
            if err: return None, err
            left = BinOpNode(center, left, right)

        return left, None


    def term(self) -> tuple[Node | None, Exception | None]:

        left, err = self.factor()

        if left == 'theend': return left, err
        if err: return None, err

        while (self.cur_tok != self.EOE
        and self.cur_tok.type in(
            T_MUL, T_DIV, T_RPAN1
        )):

            if self.cur_tok == T_RPAN1:
                return left, None

            center = self.cur_tok.type
            eof, err = self.next_tok()

            if eof:
                return "theend", Exception("expected more tokens")
            elif err:
                return None, err

            right, err = self.factor()

            if right == 'theend': return right, err
            if err: return None, err
            left = BinOpNode(center, left, right)

        return left, None


    def factor(self) -> tuple[Node | None, Exception | None]:

        t = self.cur_tok

        if t.type in (T_ADD, T_SUB):

            eof, err = self.next_tok()

            if eof:
                return "theend", Exception("expected more tokens")
            elif err:
                return None, err
            
            res, err = self.factor()

            if res == 'theend': return res, err
            if err:return None, err

            if t == T_SUB:
                return NegNode(res),None

            else:
                return PosNode(res), None


        elif t == T_LPAN1:
            eof, err = self.next_tok()

            if eof:
                return "theend", Exception("expected more tokens")
            elif err:
                return None, err
            
            return self.compare_expr()

        elif t == T_LITERAL:
            #a common factor
            eof, err = self.next_tok()

            if eof:
                return "theend", Exception("expected more tokens")
            elif err:
                return None, err

            if t.typer in ("int","float"):
                return ConstantNode(t.value, t.typer), None

            elif t.typer == "bool":
                return ConstantNode(1 if t.value == "true" else 0, "bool"), None


        elif t == T_IDEN:

            iden = t.value
            eof, err = self.next_tok()

            if eof:
                return "theend", Exception("expected more tokens")

            elif err:
                return None, err

            if self.cur_tok == T_LPAN1:
                pass #this is a call

            #else
            if iden in self.ctx.variables_ptr:

                return VarFetchNode(
                    self.ctx.variables_ptr[iden]["value"],
                    self.ctx.variables_ptr[iden]["type"]
                ), None

            else:
                return None, Exception(f"unknown variable {iden}")


        return None, Exception(f"invalid token {t}")



    def expect(self, *v, isType = True) -> Exception | None:

        if isType:
            if not self.cur_tok.type in v:
                return Exception(f"expected {v} as type")
        else:
            if not self.cur_tok.value in v:
                return Exception(f"expected {v} as value")
        return None
        

    def parse_var(self) -> tuple[Node | None, Exception | None]:

        eof, err = self.next_tok()

        if eof:
            return "theend", Exception("expected more tokens")
        elif err:
            return None, err            

        if err := self.expect(T_IDEN):
            return None, err

        var_name = self.cur_tok.value
        var_type = 0
        var_expr = 0

        eof, err = self.next_tok()

        if eof:
            return "theend", Exception("expected more tokens")
        elif err:
            return None, err

        if self.cur_tok == T_COLON:
        
            eof, err = self.next_tok()

            if eof:
                return "theend", Exception("expected more tokens")
            elif err:
                return None, err

            if err := self.expect(
                "int", "char", "short", "bool", #integer types
                "float", "double", #floating point types
                isType=False
            ): return None, err

            var_type = self.cur_tok.value
            eof, err = self.next_tok()

            if eof:
                return "theend", Exception("expected more tokens")
            elif err: 
                return None, err

        if self.cur_tok == T_EQ:
            eof, err = self.next_tok()

            if eof:
                return "theend", Exception("expected more tokens")
            elif err:
                return None, err

            var_expr, err = self.compare_expr()

            if var_expr == 'theend': return var_expr, err
            if err: return None, err

        if err := self.expect(T_EOS):
            return None, err


        end_idx = self.cur_pos
        eof, err = self.next_tok() #consume EOS

        if err:
            return None, err        

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

        eof, err = self.next_tok()

        if eof:
            return "theend", Exception("expected more tokens")

        elif err:
            return None, err

        expression, err = self.compare_expr()

        if expression == 'theend': return expression, err
        if err: return None, err

        if err := self.expect(T_EOS):
            return None, err

        end_idx = self.cur_pos
        eof, err = self.next_tok() #consume EOS

        if eof:
            return "theend", None
        elif err:
            return None, err

        if iden in self.ctx.variables_ptr:

            #cutting the last successful node
            self.tokens = cutOut(self.tokens, self.node_start, end_idx)
            #from current position to end remains

            #fix the index pointer
            self.cur_pos = self.node_start

            return VarAssignNode(
                self.ctx.variables_ptr[iden]["value"],
                expression,
                self.ctx.variables_ptr[iden]["type"]
            ), None

        #else
        return None, Exception(f"unknow identifier {iden}")

    def parse_if(self):
    
        eof, err = self.next_tok()
        
        if eof:
            return "theend", Exception("expected condition after if")

        elif err:
            return None, err

        #adjusting the end point of expr
        pre_eoe = self.EOE
        self.EOE = T_COLON

        start_pos = self.node_start
        
        cond_expr, err = self.compare_expr()

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
            return "theend" , Exception("excepted at least end keyword to close the if block")

        elif err:
            return None, err

        self.EOE = pre_eoe #back to previous

        while self.cur_tok.value not in (
            "end", "elif", "else"
        ):
            res, err = self.router()

            if res == 'theend':
                return res, err
            elif err: 
                return None, err

            self.cache.append((self.indent, res))

        if self.cur_tok == T_EOF:
            return None, Exception("excepted at least \"end\" to close the if block")

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

        # cut out
        self.tokens = cutOut(self.tokens, start_pos, self.cur_pos-1)
        # fix the position pointer
        self.cur_pos = start_pos
        
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

        self.tokens = cutOut(self.tokens, end_idx, end_idx)
        # fixing the pointer
        self.cur_pos = end_idx

        return current_block, None
    #end

    def parse_else(self):

        eof, err = self.next_tok() #consume else key

        if eof:
            return "theend", Exception("expected more tokens")
        elif err:
            return None, err

        if err := self.expect(T_COLON):
            return None, err

        eof, err = self.next_tok() # consume the colon

        if eof:
            return 'theend', Exception("expected more tokens")

        elif err:
            return None, err

        start_pos = self.node_start

        while self.cur_tok.value != "end":
            res, err = self.router()

            if res == 'theend': 
                return res, Exception("excepted at least \"end\" to close the if block")

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

        # cut out
        self.tokens = cutOut(self.tokens, start_pos, end_pos)
        self.cur_pos = start_pos

        return current_block, None

    def router(self) -> tuple[ MyBlock | Node , Exception]:
    
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
                return "theend", Exception(f"excepted more tokens after {iden_name}")
            elif err:
                return None, err

            #means this is a assign node
            if self.cur_tok == T_EQ:
                return self.parse_assign(iden_name)

            #this is a call node
            elif self.cur_tok == T_LPAN1:
                pass

        return "theend", None


    def parse(self) -> tuple[Node | None, Exception | None]:

        if err := self.consume():
            return None, err

        self.cur_pos = -1
        #one step before the original
        #because it will currect itself
        eof, err = self.next_tok()

        if eof:
            return "theend", None
        elif err:
            return None, err

        return self.router()

    #end function

#end class

