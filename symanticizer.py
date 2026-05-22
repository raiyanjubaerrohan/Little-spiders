from nodes import *
from llvmlite.ir import FloatType, IntType, DoubleType

class Symantics:

    def load(self, ast):
        self.cur_node = ast


    def simanticize(self, exp_type = "") -> tuple[str | int, Node]:

        if isinstance(self.cur_node, VarDeclareNode):

            varDec = self.cur_node
            self.cur_node = varDec.expr
            exp_type = varDec.llvm_type

            exp_type,expression = self.simanticize(exp_type)

            if exp_type and expression:
            
                if exp_type  == "int":
                    varDec.llvm_type = IntType(32)
                    expression.llvm_type = IntType(32)

                elif exp_type == "char":
                    varDec.llvm_type = IntType(8)
                    expression.llvm_type = IntType(8)

                elif exp_type == "short":
                    varDec.llvm_type = IntType(16)
                    expression.llvm_type = IntType(16)
                    
                elif exp_type == "float":
                    varDec.llvm_type = FloatType()
                    expression.llvm_type = FloatType()

                elif exp_type == "double":
                    varDec.llvm_type = DoubleType()
                    expression.llvm_type = DoubleType()

                varDec.expr = expression

                return 0, varDec

            else:
                raise Exception("""
                something went wrong.
                Please note that this is under development.
                enter the debug mode to spot the problem.
                (only for developer)
                """)

        elif isinstance(self.cur_node, VarAssignNode):
            node = self.cur_node
            exp_type = self.cur_node.llvm_type

            self.cur_node = node.expr
            exp_type, typed_ast = self.simanticize(exp_type)

            if exp_type == "int":
                typed_ast.llvm_type = IntType(32)

            elif exp_type == "char":
                typed_ast.llvm_type = IntType(8)

            elif exp_type == "short":
                typed_ast.llvm_type = IntType(16)

            elif exp_type == "float":
                typed_ast.llvm_type = FloatType()

            elif exp_type == "double":
                typed_ast.llvm_type = DoubleType()

            return 0,VarAssignNode(
                node.value,
                typed_ast,
                exp_type
            )
        
        elif isinstance(self.cur_node, BinOpNode):

            tree = self.cur_node
            self.cur_node = tree.lhs
            _, ty_lhs = self.simanticize(exp_type)

            self.cur_node = tree.rhs
            _, ty_rhs = self.simanticize(exp_type)

            exp_type, ty_lhs, ty_rhs = self.align_type(
                ty_lhs,
                ty_rhs,
                exp_type
            )

            binOp = BinOpNode(
                tree.value,
                ty_lhs, 
                ty_rhs
            )

            if exp_type == "int":
                binOp.llvm_type = IntType(32)

            elif exp_type == "char":
                binOp.llvm_type = IntType(8)

            elif exp_type == "short":
                binOp.llvm_type = IntType(16)

            elif exp_type == "float":
                binOp.llvm_type = FloatType()

            elif exp_type == "double":
                binOp.llvm_type = DoubleType()

            else:
                raise Exception("something went wrong, from symanticizer")

            return exp_type, binOp


        elif isinstance(self.cur_node, (ConstantNode, VarFetchNode)) :
        
            if not exp_type:
                return self.cur_node.llvm_type, self.cur_node

            elif exp_type == "int":
            
                return self.select_type(
                    IntType(32),
                    "int",
                    float=CastFloToInt,
                    char=CastIntHigh,
                    short=CastIntHigh
                )


            elif exp_type == "char":

                return self.select_type(
                    IntType(8),
                    "char",
                    float=CastFloToInt,
                    int=CastIntLow,
                    short=CastIntLow
                )


            elif exp_type == "short":

                return self.select_type(
                    IntType(16),
                    "short",
                    int=CastIntLow,
                    char=CastIntHigh,
                    float=CastFloToInt
                )

            elif exp_type == "float":

                return self.select_type(
                    FloatType(),
                    "float",
                    int=CastIntToFlo,
                    char=CastIntToFlo,
                    short=CastIntToFlo
                )

            return 0, None
            #end

        elif isinstance(self.cur_node, NegNode):
            node = self.cur_node
            self.cur_node = node.value
            exp_type, node = self.simanticize(exp_type)
            node.llvm_type = exp_type

            return exp_type, NegNode(node)

        elif isinstance(self.cur_node, PosNode):
            node = self.cur_node
            self.cur_node = node.value
            exp_type, node = self.simanticize(exp_type)
            node.llvm_type = exp_type

            return exp_type, PosNode(node)
        #end

        return 0, None


    def align_type(self, lhs, rhs, exp_type):
        if exp_type:
            return exp_type, lhs, rhs
            
        else: 
            if "float" in (
                lhs.llvm_type,
                rhs.llvm_type
            ):
                #equal to
                #lhs or rhs is "float"
                if lhs == "int":
                    lhs.llvm_type = IntType(32)
                    lhs = CastIntToFlo(lhs, FloatType())

                elif lhs == "char":
                    lhs.llvm_type = IntType(8)
                    lhs = CastIntToFlo(lhs, FloatType())

                else:
                    lhs.llvm_type = FloatType()

                if rhs == "int":
                    rhs.llvm_type = IntType(32)
                    rhs = CastIntToFlo(rhs, FloatType())

                elif rhs == "char":
                    rhs.llvm_type = IntType(8)
                    rhs = CastIntToFlo(rhs, FloatType())

                else:
                    rhs.llvm_type = FloatType()

                return "float", lhs, rhs

            elif "int" in (lhs.llvm_type, rhs.llvm_type):
            
                if lhs == "char":
                    lhs.llvm_type = IntType(8)
                    lhs = CastIntHigh(lhs, IntType(32))

                if rhs == "char":
                    rhs.llvm_type = IntType(8)
                    rhs = CastIntHigh(rhs, IntType(32))

            return "int", lhs, rhs

        #end
    #end

    def select_type(
        self,
        base_type, # llvm type instance
        base_str,
        **cast_types #the reference of casting type
    ):

        current_type = ""
    
        if self.cur_node.llvm_type == "int":
            self.cur_node.llvm_type = IntType(32)
            current_type = "int"

        elif self.cur_node == "char":
            self.cur_node.llvm_type = IntType(8)
            current_type = "char"
            

        elif self.cur_node == "short":
            self.cur_node.llvm_type = IntType(16)
            current_type = "short"

        elif self.cur_node == "float":
            self.cur_node.llvm_type = FloatType()
            current_type = "float"

        elif self.cur_node != base_str:
            raise Exception(f"unable to cast {self.cur_node}")

        if current_type in cast_types:
            return base_str, cast_types[current_type](
                self.cur_node,
                base_type
            )

        #else
        return base_type, self.cur_node

    #end
#end

        
