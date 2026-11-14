from nodes import (
    NegNode,
    NotNode,
    StringNode,
    BitNode,
    ConstantNode,
    BinOpNode,
    BitOpNode,
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
    CallNode,
    BreakNode,
    ContinueNode,
    IfElseBlock,
    ElseBlock,
    WhileBlock,
)

from utils import Symbol, T_POISON
from diagnostical import Diagnostics

class Resolver:
    def __init__(self, diagctx):
        self.cur_node = None
        self.scope = 0
        self.variables_ptr = [{}]
        self.ctx = None
        self.diagctx = diagctx

    def load(self, ast, ctx):
        self.cur_node = ast
        self.ctx = ctx

    def resolve(self) -> Node | str:
        tree = self.cur_node

        if tree == T_POISON: return T_POISON

        if isinstance(tree, (
            BreakNode,
            ContinueNode,
            StringNode,
            ConstantNode,
            BitNode
        )):
            return tree

        if isinstance(tree, (NegNode, NotNode)):
            self.cur_node = tree.value
            res = self.resolve()
            if res == T_POISON: return T_POISON

            return type(tree)(res, tree.span) # a python hack

        if isinstance(tree, CallNode):

            # first resolve the params
            params = []
            for self.cur_node in tree.params:
                expr = self.resolve()
                if expr == T_POISON: return T_POISON
                params.append(expr)

            # now the value and return type
            if tree.value in self.ctx.function_ptr:

                call_node = CallNode(
                    self.ctx.function_ptr[tree.value]["value"],
                    params,
                    tree.span
                )
                call_node.llvm_type = self.ctx.function_ptr[tree.value]["type"]
                call_node.name = tree.value

                return call_node
                
            self.diagctx.emit(Diagnostics(
                f"there is no such function as {tree.value}",
                "R0492",
                tree.span
                # help "did you mean...?"
            ))
            return T_POISON

        if isinstance(tree, (BinOpNode, BitOpNode, CompareNode)):

            # lhs
            self.cur_node = tree.lhs
            res_lhs = self.resolve()
            if res_lhs == T_POISON: return T_POISON

            # rhs
            self.cur_node = tree.rhs
            res_rhs = self.resolve()
            if res_rhs == T_POISON: return T_POISON

            return type(tree)(tree.value, res_lhs, res_rhs, tree.span)

        if isinstance(tree, (
            CastIntToFlo,
            CastFloToInt,
            CastIntLow,
            CastIntHigh,
            CastFloLow,
            CastFloHigh
        )):
            self.cur_node = tree.value
            res = self.resolve()
            if res == T_POISON: return T_POISON

            return type(tree)(res, tree.span)

        if isinstance(self.cur_node, VarAssignNode):

            self.cur_node = tree.expr
            temp_expr = self.resolve()
            if temp_expr == T_POISON: return T_POISON

            for sp in reversed(range(self.scope+1)):
                dict_of_scope = self.variables_ptr[sp]

                # for now tree.value is the name
                if tree.value in dict_of_scope:
                    return VarAssignNode(
                        dict_of_scope[tree.value],
                        temp_expr,
                        tree.span
                    )

            # the loop only comes here if it
            # do not found the name in any lower scope.
            # means, it is an exception

            self.diagctx.emit(Diagnostics(
                f"the variable {tree.value} is not declared "
                "or not valid on this scope",
                "R0478",
                tree.span
            ))
            return T_POISON

        if isinstance(tree, VarDeclareNode):

            self.cur_node = tree.expr
            temp_expr = self.resolve() if self.cur_node else 0
            if temp_expr == T_POISON: return T_POISON

            # linking entry
            tree.value = Symbol(tree.value, tree.llvm_type)

            # the latest scope entry
            self.variables_ptr[-1][tree.value.name] = tree.value

            return VarDeclareNode(
                tree.value,
                tree.span,
                tree.llvm_type,
                temp_expr
            )

        if isinstance(tree, VarFetchNode):

            for sp in reversed(range(self.scope+1)):
                dict_of_scope = self.variables_ptr[sp]

                if tree.value in dict_of_scope:
                    return VarFetchNode(dict_of_scope[tree.value], tree.span)

            # same reason as varAssignNode
            self.diagctx.emit(Diagnostics(
                f"the variable {tree.value} is not declared "
                "or not valid on this scope",
                "R0478",
                tree.span
            ))
            return T_POISON

        if isinstance(tree, (IfElseBlock)):
            # condition
            self.cur_node = tree.cond
            cond_expr = self.resolve()

            # increse the scope
            self.scope += 1
            self.variables_ptr.append({})

            # body
            nodes = []
            for self.cur_node in tree.body:
                nodes.append(self.resolve())

            # desreasing the scope for the else block
            self.scope -= 1
            self.variables_ptr.pop()

            # else block
            self.cur_node = tree.else_block
            else_block = self.resolve()

            return type(tree)(cond_expr, nodes, else_block, tree.span)

        if isinstance(tree, ElseBlock):

            # increse the scope
            self.scope += 1
            self.variables_ptr.append({})

            # body
            nodes = []
            for self.cur_node in tree.body:
                nodes.append(self.resolve())

            # returing from else block, we should decrease scope
            self.scope -= 1
            self.variables_ptr.pop()

            return ElseBlock(nodes, tree.span)

