from nodes import (
    Node,
    NegNode,
    PosNode,
    ConstantNode,
    StringNode,
    BinOpNode,
    CompareNode,
    CastFloToInt,
    CastIntToFlo,
    CastIntHigh,
    CastIntLow,
    CastFloLow,
    CastFloHigh,
    VarAssignNode,
    VarDeclareNode,
    VarFetchNode,
    DefaultBlock,
    IfElseBlock,
    ElseBlock,
)

from utils import Context

class Resolver:
    def __init__(self):
        self.cur_node = None
        self.scope = 0
        self.ctx = None
        self.max_scope = 0

    def load(self, ast, ctx: Context):
        self.cur_node = ast
        self.ctx = ctx 

    def resolve(self) -> tuple[
        Context | None,
        Exception | None
    ]:

        if isinstance(self.cur_node, (NegNode, PosNode)):
            tree = self.cur_node
            self.cur_node = tree.value

            return self.resolve()

        elif isinstance(self.cur_node, (BinOpNode, CompareNode)):
            tree = self.cur_node

            # for lhs
            self.cur_node = tree.lhs
            self.ctx, err = self.resolve()
            if err: return None, err
            

            # for rhs
            self.cur_node = tree.rhs
            self.ctx, err = self.resolve()
            if err: return None, err

        elif isinstance(self.cur_node, (
            CastIntToFlo,
            CastFloToInt,
            CastIntLow,
            CastIntHigh,
            CastFloLow,
            CastFloHigh
        )):
            tree = self.cur_node

            self.cur_node = tree.value

            return self.resolve()

        elif isinstance(self.cur_node, VarAssignNode):
            tree = self.cur_node

            self.cur_node = tree.expr
            self.ctx, err = self.resolve()
            if err: return None, err

            for sp in reversed(range(self.scope+1)):
                dict_of_scope = self.ctx.variables_ptr[sp]

                if tree.value in dict_of_scope:
                    # we should store the key in a temporary variaable
                    key = tree.value
                    
                    tree.value = dict_of_scope[key]["value"]
                    tree.llvm_type = dict_of_scope[key]["type"]
                    return self.ctx, None

            # the loop only comes here if it 
            # do not found the name in any lower scope
            # means, it is an exception

            return None, Exception(
                "the variable {tree.value} is not declared "
                "or not valid on this scope"
            )

        elif isinstance(self.cur_node, VarDeclareNode):
            tree = self.cur_node

            tree.scope = self.scope

            self.cur_node = tree.expr
            self.ctx, err = self.resolve()
            if err: return None, err

            # I realize that we do not have to
            # create an entry for the variable

        elif isinstance(self.cur_node, VarFetchNode):
            tree = self.cur_node

            for sp in reversed(range(self.scope+1)):
                dict_of_scope = self.ctx.variables_ptr[sp]

                if tree.value in dict_of_scope:

                    key = tree.value
                    
                    tree.value = dict_of_scope[key]["value"]
                    tree.llvm_type = dict_of_scope[key]["type"]
                    return self.ctx, None

            # same reason as varAssignNode
            return None, Exception(
                "the variable {tree.value} is not declared "
                "or not valid on this scope"
            )

        elif isinstance(self.cur_node, IfElseBlock):
            tree = self.cur_node

            # condition
            self.cur_node = tree.cond
            self.ctx, err = self.resolve()
            if err: return None, err

            # before entering the body we should increse the scope
            self.scope += 1
            self.max_scope += 1
            
            self.ctx.variables_ptr.append({})

            # body
            for self.cur_node in tree.body:
                self.ctx, err = self.resolve()
                if err: return None, err

            # desreasing the scope for the else block
            self.scope -= 1

            # else block
            self.cur_node = tree.else_block
            self.ctx, err = self.resolve()
            if err: return None,err

        elif isinstance(self.cur_node, ElseBlock):
            tree = self.cur_node

            # increse the scope
            self.scope += 1
            self.max_scope += 1
            
            self.ctx.variables_ptr.append({})

            # body
            for self.cur_node in tree.body:
                self.ctx, err = self.resolve()
                if err: return None, err

            # returing from else block, we should decrease scope
            self.scope -= 1

        if len(self.ctx.variables_ptr) != self.max_scope + 1:
            return None, Exception(
                "something went wrong\n"
                "please enter debug mode to solve.\n"
                "(developers only)"
            )

        return self.ctx, None
