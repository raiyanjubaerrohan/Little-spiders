from nodes import *
from llvmlite.ir import FloatType, IntType

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
            
                if exp_type in ("int", "intiger"):
                #equals to exp_type == "int" or exp_type == "intiger"
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

            if exp_type in ("int","intiger"):
                typed_ast.llvm_type = IntType(32)

            elif exp_type == "char":
                typed_ast.llvm_type = IntType(8)

            elif exp_type == "short":
                typed_ast.llvm_type = IntType(16)

            elif exp_type == "float":
                typed_ast.llvm_type = FloatType()

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

            else:
                raise Exception("something went wrong, from symanticizer")

            return exp_type, binOp


        elif isinstance(self.cur_node, (ConstantNode, VarFetchNode)) :
        
            if not exp_type:
                return self.cur_node.llvm_type, self.cur_node

            elif exp_type == "int":
            
                if self.cur_node == "float":
                
                    self.cur_node.llvm_type = FloatType()
                    return "int", CastFloToInt(
                        self.cur_node,
                        IntType(32)
                    )

                elif self.cur_node == "char":

                    self.cur_node.llvm_type = IntType(8)
                    return "int", CastIntHigh(
                        self.cur_node,
                        IntType(32)
                    )

                elif self.cur_node == "short":

                    self.cur_node.llvm_type = IntType(16)
                    return "int", CastIntHigh(
                        self.cur_node,
                        IntType(32)
                    )

                elif self.cur_node != "intiger":
                    raise Exception(
                        f"can not convert type {self.cur_node}"
                    )

                self.cur_node.llvm_type = IntType(32)
                
                return "int",self.cur_node


            elif exp_type == "char":

                if self.cur_node == "float":
                    self.cur_node.llvm_type = FloatType()
                    return "char", CastFloToInt(
                        self.cur_node,
                        IntType(8)
                    )

                elif self.cur_node.llvm_type in ("intiger","int"):
                    self.cur_node.llvm_type = IntType(32)
                    return "char", CastIntLow(
                        self.cur_node,
                        IntType(8)
                    )

                elif self.cur_node == "short":
                    self.cur_node.llvm_type = IntType(16)
                    return "char", CastIntLow(
                        self.cur_node,
                        IntType(8)
                    )

                self.cur_node.llvm_type = IntType(8)

                return "char", self.cur_node


            elif exp_type == "short":

                if self.cur_node.llvm_type in ("intiger", "int"):
                    self.cur_node.llvm_type = IntType(32)
                    return "short", CastIntLow(
                        self.cur_node,
                        IntType(16)
                    )

                elif self.cur_node == "char":
                    self.cur_node.llvm_type = IntType(8)
                    return "short", CastIntHigh(
                        self.cur_node,
                        IntType(16)
                    )

                elif self.cur_node == "float":
                    self.cur_node.llvm_type = FloatType()
                    return "short", CastFloToInt(
                        self.cur_node,
                        IntType(16)
                    )

                self.cur_node.llvm_type = IntType(16)
                return "short", self.cur_node

            elif exp_type == "float":

                if self.cur_node.llvm_type in ("intiger","int"):
                    self.cur_node.llvm_type = IntType(32)

                    return "float",CastIntToFlo(
                        self.cur_node,
                        FloatType()
                    )

                elif self.cur_node == "char":
                    self.cur_node.llvm_type = IntType(8)

                    return "float", CastIntToFlo(
                        self.cur_node,
                        FloatType()
                    )

                elif self.cur_node == "short":
                    self.cur_node.llvm_type = IntType(16)

                    return "float", CastIntToFlo(
                        self.cur_node,
                        FloatType()
                    )

                elif self.cur_node != "float":
                    raise Exception(
                        f"can not convert type {self.cur_node}"
                    )

                self.cur_node.llvm_type = FloatType()
                return "float",self.cur_node

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
                if lhs == "intiger":
                    lhs.llvm_type = IntType(32)
                    lhs = CastIntToFlo(lhs, FloatType())

                elif lhs == "char":
                    lhs.llvm_type = IntType(8)
                    lhs = CastIntToFlo(lhs, FloatType())

                else:
                    lhs.llvm_type = FloatType()

                if rhs == "intiger":
                    rhs.llvm_type = IntType(32)
                    rhs = CastIntToFlo(rhs, FloatType())

                elif rhs == "char":
                    rhs.llvm_type = IntType(8)
                    rhs = CastIntToFlo(rhs, FloatType())

                else:
                    rhs.llvm_type = FloatType()

                return "float", lhs, rhs

            elif ("intiger" in (lhs.llvm_type, rhs.llvm_type)
            or "int" in (lhs.llvm_type, rhs.llvm_type)):
            
                if lhs == "char":
                    lhs.llvm_type = IntType(8)
                    lhs = CastIntHigh(lhs, IntType(32))

                if rhs == "char":
                    rhs.llvm_type = IntType(8)
                    rhs = CastIntHigh(rhs, IntType(32))

            return "int", lhs, rhs

        #end
    #end

#end

        
