from nodes import *
from llvmlite.ir import DoubleType, IntType

class Symantics:
    def __init__(self, ast):
        self.cur_node = ast


    def simanticize(self, exp_type = "") -> tuple[str | int, Node]:

        if isinstance(self.cur_node, VarDeclareNode):

            varDec = self.cur_node
            self.cur_node = varDec.expr
            exp_type = varDec.llvm_type

            exp_type,expression = self.simanticize(exp_type)

            if exp_type and expression:
            
                if exp_type == "int":
                    varDec.llvm_type = IntType(32)
                    expression.llvm_type = IntType(32)
                elif exp_type == "float":
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

            binOp.llvm_type = exp_type

            return exp_type, binOp


        elif isinstance(self.cur_node, ConstantNode):
            if not exp_type:
                return self.cur_node.llvm_type, self.cur_node

            elif exp_type == "int":
            
                if self.cur_node == "float":
                    self.cur_node.llvm_type = DoubleType()

                    return "int", CastFloToInt(self.cur_node)

                elif self.cur_node != "intiger":
                    raise Exception(
                        f"can not convert type {self.cur_node}"
                    )
                    
                return "int",self.cur_node

            elif exp_type == "float": 

                if self.cur_node == "intiger":
                    self.cur_node.llvm_type = IntType(32)

                    return "float",CastIntToFlo(self.cur_node)

                elif self.cur_node != "float":
                    raise Exception(
                        f"can not convert type {self.cur_node}"
                    )

                return "float",self.cur_node

            #end

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
                if lhs == "intiger":
                    lhs.llvm_type = IntType(32)
                    lhs = CastIntToFlo(lhs)

                else:
                    lhs.llvm_type = DoubleType()

                if rhs == "intiger":
                    rhs.llvm_type = IntType(32)
                    rhs = CastIntToFlo(rhs)

                else:
                    rhs.llvm_type = DoubleType()

                return "float", lhs, rhs

            #elif rhs or lhs == "intiger":
            lhs.llvm_type = IntType(32)
            rhs.llvm_type = IntType(32)

            return "int", lhs, rhs

        #end
    #end

#end

        
