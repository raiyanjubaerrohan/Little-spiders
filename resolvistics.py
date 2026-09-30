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

from utils import Symbol

class Resolver:
    def __init__(self):
        self.cur_node = None
        self.scope = 0
        self.variables_ptr = [{}]

    def load(self, ast):
        self.cur_node = ast

        # removing all the items except first one
        fir = self.variables_ptr[0]
        self.variables_ptr = []

        self.variables_ptr.append(fir)

        # we did not remove the first one
        # because it will later ruin the global scope

    def resolve(self) -> Exception | None:
        tree = self.cur_node

        if isinstance(tree, (NegNode, PosNode)):
            self.cur_node = tree.value

            return self.resolve()

        elif isinstance(tree, (BinOpNode, CompareNode)):

            # for lhs
            self.cur_node = tree.lhs
            if err := self.resolve(): return err
            

            # for rhs
            self.cur_node = tree.rhs
            if err := self.resolve(): return err

        elif isinstance(tree, (
            CastIntToFlo,
            CastFloToInt,
            CastIntLow,
            CastIntHigh,
            CastFloLow,
            CastFloHigh
        )):
            self.cur_node = tree.value

            return self.resolve()

        elif isinstance(self.cur_node, VarAssignNode):

            self.cur_node = tree.expr
            if err := self.resolve(): return err

            for sp in reversed(range(self.scope+1)):
                dict_of_scope = self.variables_ptr[sp]

                # for now tree.value is the name
                if tree.value in dict_of_scope:
                
                    tree.value = dict_of_scope[tree.value]
                    #now it a symbol instant
                    
                    return None

            # the loop only comes here if it 
            # do not found the name in any lower scope
            # means, it is an exception

            return Exception(
                "the variable {tree.value} is not declared "
                "or not valid on this scope"
            )

        elif isinstance(tree, VarDeclareNode):

            tree.scope = self.scope

            self.cur_node = tree.expr
            if err := self.resolve(): return err

            # linking entry
            temp = tree.value
            tree.value = Symbol()
            tree.value.name = temp
            tree.value.llvm_type = tree.llvm_type

            # the latest scope entry
            self.variables_ptr[-1][tree.value.name] = tree.value
            

        elif isinstance(tree, VarFetchNode):

            for sp in reversed(range(self.scope+1)):
                dict_of_scope = self.variables_ptr[sp]

                if tree.value in dict_of_scope:
                
                    tree.value = dict_of_scope[tree.value]
                    # now tree.value is a symbol instant
                    
                    return None

            # same reason as varAssignNode
            return Exception(
                "the variable {tree.value} is not declared "
                "or not valid on this scope"
            )

        elif isinstance(tree, IfElseBlock):
            # condition
            self.cur_node = tree.cond
            if err := self.resolve(): return err

            # before entering the body we should increse the scope
            self.scope += 1
            
            self.variables_ptr.append({})

            # body
            for self.cur_node in tree.body:
                if err := self.resolve(): return err

            # desreasing the scope for the else block
            self.scope -= 1
            self.variables_ptr.pop()

            # else block
            self.cur_node = tree.else_block
            if err := self.resolve(): return err

        elif isinstance(tree, ElseBlock):

            # increse the scope
            self.scope += 1

            self.ctx.variables_ptr.append({})

            # body
            for self.cur_node in tree.body:
                if err := self.resolve(): return err

            # returing from else block, we should decrease scope
            self.scope -= 1
            self.variables_ptr.pop()

        return None
