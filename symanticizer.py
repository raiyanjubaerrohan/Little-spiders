from nodes import *
from llvmlite.ir import FloatType, IntType, DoubleType,  PointerType

class Symantics:

    def __init__(self):
        self.cur_node = None
        self.exp_type = None

    def load(self, ast):
        self.cur_node = ast

    def simanticize_varDecNode(self) -> tuple[Node | None, Exception | None]:
        
        varDec = self.cur_node
        self.cur_node = varDec.expr
        self.exp_type = varDec.llvm_type
        
        expr, err = self.simanticize()
        if err: return None, err

        if expr and self.exp_type:
            res, err = self.get_currect_type()
            if err: return None, err

            varDec.llvm_type = res
            expr.llvm_type = res

            varDec.expr = expr

            return varDec, None

        return None, Exception("can not find a type for the variable")

    def simanticize_varAssNode(self) -> tuple[Node | None, Exception | None]:

        node = self.cur_node
        self.exp_type = node.llvm_type

        self.cur_node = node.expr
        expr, err = self.simanticize()
        if err: return None, err

        res, err = self.get_currect_type()
        if err: return None, err

        expr.llvm_type = res

        return VarAssignNode(node.value, expr, self.exp_type), None

    def simanticize_binOpNode(self):

        tree = self.cur_node

        ### lhs
        self.cur_node = tree.lhs
        res_lhs, err = self.simanticize()
        if err: return None, err
        elif self.exp_type == "string":
            return None, Exception("can not do operation with string")

        ### rhs
        self.cur_node = tree.rhs
        res_rhs, err = self.simanticize()
        if err: return None, err
        elif self.exp_type == "string":
            return None, Exception("can not do operation with string")

        ty_lhs, ty_rhs, err = self.align_type(
            res_lhs,
            res_rhs
        )
        if err: return None, err

        binOp = BinOpNode(tree.value, ty_lhs, ty_rhs)

        res, err = self.get_currect_type()
        if err: return None, err

        binOp.llvm_type = res

        return binOp, None


    def simanticize_compareNode(self):

        tree = self.cur_node

        ### lhs
        self.cur_node = tree.lhs
        res_lhs, err = self.simanticize()
        if err: return None, err
        elif self.exp_type == "string":
            return None, Exception("can not compare string")

        ### rhs
        self.cur_node = tree.rhs
        res_rhs, err = self.simanticize()
        if err: return None, err
        elif self.exp_type == "string":
            return None, Exception("can not compare string")

        ty_lhs, ty_rhs, err = self.align_type(
            res_lhs,
            res_rhs
        )
        if err: return None, err

        cmpNode = CompareNode(tree.value, ty_lhs, ty_rhs)

        cmpNode.llvm_type = "bool"
        cmpNode.mean_type = self.exp_type

        self.exp_type = "bool"

        return cmpNode, None

    def simanticize(self) -> tuple[Node | None, Exception | None]:

        if isinstance(self.cur_node, VarDeclareNode):

            res, err = self.simanticize_varDecNode()
            if err: return None, err

            return res, None

        elif isinstance(self.cur_node, VarAssignNode):

            res, err = self.simanticize_varAssNode()
            if err: return None, err

            return res, None
        
        elif isinstance(self.cur_node, BinOpNode):
        
            res, err = self.simanticize_binOp()
            if err: return None, err

            return res, None

        elif isinstance(self.cur_node, CompareNode):

            res, err = self.simanticize_compareNode()
            if err: return None, err

            return res, None

        elif isinstance(self.cur_node, (ConstantNode, VarFetchNode)):
            self.exp_type = self.cur_node.llvm_type
            
            return self.cur_node, None
            #end

        elif isinstance(self.cur_node, NegNode):
            node = self.cur_node
            self.cur_node = node.value
            node, err = self.simanticize()
            if err: return None, err
            
            node.llvm_type = self.get_currect_type(exp_type)

            return NegNode(node), None

        elif isinstance(self.cur_node, PosNode):
            node = self.cur_node
            self.cur_node = node.value
            node, err = self.simanticize()
            if err: return None, err
            
            node.llvm_type = self.get_currect_type(exp_type)

            return PosNode(node), None

        elif isinstance(self.cur_node, StringNode):
            self.exp_type = "string"
            return self.cur_node, None

        elif isinstance(self.cur_node, IfElseBlock):

            res, err = self.simanticize()
            if err : return None, err

            return res, None

        elif isinstance(self.cur_node, ElseBlock):

            res, err = self.simanticize_ElseBlock()
            if err: return None, err

            return res, None

        elif isinstance(self.cur_node, DefaultBlock):
            return self.cur_node, None
            
        #end
        return None, Exception("no object matched the list")

    def simanticize_ifElseBlock(self) -> tuple[IfElseBlock | None, Exception | None]:

        if_block = self.cur_node

        # the condition
        self.cur_node = if_block.cond
        res_cond, err = self.simanticize()
        if err: return None, err

        # the body
        stmts = []

        for stm in if_block.body:
            self.cur_node = stm

            res, err = self.simanticize()
            if err: return None, err

            stmts.append(res)

        # the else block
        self.cur_node = if_block.else_block
        res_else_block, err = self.simanticize()
        if err: return None, err

        return IfElseBlock(res_cond, stmts, res_else_block)

    def simanticize_ElseBlock(self):

        else_block = self.cur_node

        stmts = []

        for stm in else_block.body:
            self.cur_node = stm

            res, err = self.simanticize()
            if err: return None, err

            stmts.append(res)

        return ElseBlock(stmts), None

    def get_currect_type(self) -> tuple[
        IntType | DoubleType | FloatType | PointerType | None,
        Exception | None
    ]:
        if self.exp_type == "int":
            return IntType(32), None
            
        elif self.exp_type == "short":
            return IntType(16), None
            
        elif self.exp_type == "char":
            return IntType(8), None
            
        elif self.exp_type == "bool":
            return IntType(1), None
            

        elif self.exp_type == "double":
            return DoubleType(), None
            
        elif self.exp_type == "float":
            return FloatType(), None
            

        elif self.exp_type == "string":
            return IntType(8).as_pointer(), None

        else:
            return None, Exception("no type matched")

    def align_type(self, lhs, rhs) -> tuple[
        Node, Node, None] | tuple[None, None, Exception
        ]:
    
        if self.exp_type:
            return lhs, rhs, None

        #the else should be sorted by dominance to be currect         
        else:
            if "double" in (lhs.llvm_type, rhs.llvm_type):
                #equals to
                #lhs or rhs is "double"

                temp = self.cur_node
                #temporary var to store the current node

                self.cur_node = lhs #for passing in select_type
                
                _, lhs = self.select_type(
                    DoubleType(),
                    "double",
                    float=CastFloHigh,
                    int=CastIntToFlo,
                    short=CastIntToFlo,
                    char=CastIntToFlo,
                    bool=CastIntToFlo
                )

                self.cur_node = rhs
                _, rhs = self.select_type(
                    DoubleType(),
                    "double",
                    float=CastFloHigh,
                    int=CastIntToFlo,
                    short=CastIntToFlo,
                    char=CastIntToFlo,
                    bool=CastIntToFlo
                )

                #at very end reassign the current node to be currect
                self.cur_node = temp
                self.exp_type = "double"

                return lhs, rhs, None
                                
            if "float" in (lhs.llvm_type, rhs.llvm_type):

                #same as upper check
                temp = self.cur_node

                self.cur_node = lhs
                _, lhs = self.select_type(
                    FloatType(),
                    "float",
                    int=CastIntToFlo,
                    short=CastIntToFlo,
                    char=CastIntToFlo,
                    bool=CastIntToFlo
                )

                self.cur_node = rhs
                _, rhs = self.select_type(
                    FloatType(),
                    "float",
                    int=CastIntToFlo,
                    short=CastIntToFlo,
                    char=CastIntToFlo,
                    bool=CastIntToFlo
                )

                self.cur_node = temp
                self.exp_type = "float"

                return lhs, rhs, None

            if "int" in (lhs.llvm_type, rhs.llvm_type):

                temp = self.cur_node

                self.cur_node = lhs
                _, lhs = self.select_type(
                    IntType(32),
                    "int",
                    short=CastIntHigh,
                    char=CastIntHigh,
                    bool=CastIntHigh
                )

                self.cur_node = rhs
                _, rhs = self.select_type(
                    IntType(32),
                    "int",
                    short=CastIntHigh,
                    char=CastIntHigh,
                    bool=CastIntHigh
                )

                self.cur_node = temp
                self.exp_type = "int"

                return lhs, rhs

            if "short" in (lhs.llvm_type, rhs.llvm_type):

                temp = self.cur_node

                self.cur_node = lhs
                _, lhs = self.select_type(
                    IntType(16),
                    "short",
                    char=CastIntHigh,
                    bool=CastIntHigh
                )

                self.cur_node = rhs
                _, rhs = self.select_type(
                    IntType(16),
                    "short",
                    char=CastIntHigh,
                    bool=CastIntHigh
                )

                self.cur_node = temp
                self.exp_type = "short"

                return lhs, rhs

            if "char" in (lhs.llvm_type, rhs.llvm_type):
                #this is different because of optimization
                if lhs == "bool":
                    lhs.llvm_type = IntType(1)
                    lhs = CastIntHigh(lhs, IntType(8))

                if rhs == "bool":
                    rhs.llvm_type = IntType(1)
                    rhs = CastIntHigh(rhs, IntType(8))

                self.exp_type = "char"

                return lhs, rhs, None

            self.exp_type = "bool" # every operand is boolean
            
            return lhs, rhs 

        #end
    #end

    def select_type(
        self,
        base_type, # llvm type instance
        base_str,
        **cast_types #the reference of casting type
    ) -> tuple[str, Node, None] | tuple[None, None, Exception]:

        current_type = ""
    
        if self.cur_node == "int":
            self.cur_node.llvm_type = IntType(32)
            current_type = "int"

        elif self.cur_node == "char":
            self.cur_node.llvm_type = IntType(8)
            current_type = "char"
            

        elif self.cur_node == "short":
            self.cur_node.llvm_type = IntType(16)
            current_type = "short"

        elif self.cur_node == "bool":
            self.cur_node.llvm_type = IntType(1)
            current_type = "bool"

        elif self.cur_node == "float":
            self.cur_node.llvm_type = FloatType()
            current_type = "float"

        elif self.cur_node == "double":
            self.cur_node.llvm_type = DoubleType()
            current_type = "double"

        elif self.cur_node == "string":
            self.cur_node.llvm_type = IntType(8).as_pointer()
            current_type = "string"

        elif self.cur_node != base_str:
            return None, None, Exception(f"unable to cast {self.cur_node}")

        if current_type in cast_types:
            return base_str, cast_types[current_type](
                self.cur_node,
                base_type
            ), None

        #else
        return base_str, self.cur_node

    #end
#end

        
