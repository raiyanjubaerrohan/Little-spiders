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

                elif exp_type == "bool":
                    varDec.llvm_type = IntType(1)
                    expression.llvm_type = IntType(1)

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

            elif exp_type == "bool":
                typed_ast.llvm_type = IntType(1)

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

            elif exp_type == "bool":
                binOp.llvm_type = IntType(1)

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

        elif isinstance(self.cur_node, CompareNode):

            tree = self.cur_node

            self.cur_node = tree.lhs
            _, typed_lhs = self.simanticize(exp_type)

            self.cur_node = tree.rhs
            _, typed_rhs = self.simanticize(exp_type)

            exp_type, ty_lhs, ty_rhs = self.align_type(
                typed_lhs,
                typed_rhs,
                exp_type
            )

            cmpNode = CompareNode(tree.value, ty_lhs, ty_rhs)

            cmpNode.llvm_type = "bool"
            cmpNode.mean_type = exp_type

            return "bool" , cmpNode

        elif isinstance(self.cur_node, (ConstantNode, VarFetchNode)):
        
            if not exp_type:
                return self.cur_node.llvm_type, self.cur_node

            elif exp_type == "int":
            
                return self.select_type(
                    IntType(32),
                    "int",
                    float=CastFloToInt,
                    double=CastFloToInt,
                    char=CastIntHigh,
                    short=CastIntHigh,
                    bool=CastIntHigh
                )


            elif exp_type == "char":

                return self.select_type(
                    IntType(8),
                    "char",
                    float=CastFloToInt,
                    double=CastFloToInt,
                    int=CastIntLow,
                    short=CastIntLow,
                    bool=CastIntHigh
                )

            elif exp_type == "bool":

                return self.select_type(
                    IntType(1),
                    "bool",
                    float=CastFloToInt,
                    double=CastFloToInt,
                    int=CastIntLow,
                    short=CastIntLow,
                    char=CastIntLow
                )


            elif exp_type == "short":

                return self.select_type(
                    IntType(16),
                    "short",
                    int=CastIntLow,
                    char=CastIntHigh,
                    float=CastFloToInt,
                    double=CastFloToInt,
                    bool=CastIntHigh
                )

            elif exp_type == "float":

                return self.select_type(
                    FloatType(),
                    "float",
                    int=CastIntToFlo,
                    char=CastIntToFlo,
                    short=CastIntToFlo,
                    double=CastFloLow,
                    bool=CastIntToFlo
                )

            elif exp_type == "double":
            
                return self.select_type(
                    DoubleType(),
                    "double",
                    int=CastIntToFlo,
                    char=CastIntToFlo,
                    short=CastIntToFlo,
                    float=CastFloHigh,
                    bool=CastIntToFlo
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


        elif isinstance(self.cur_node, IfElseBlock):
            if_block = self.cur_node

            self.cur_node = if_block.cond
            _, res = self.simanticize()

            if res is not None:
                if_block.cond = res
            else: 
                return 0, None
            
            stmts = []
            
            for stm in if_block.body:
            
                self.cur_node = stm
                _, res = self.simanticize()
                
                if res is not None:
                    stmts.append(res)
                else:
                    return 0, None

            self.cur_node = if_block.else_block
            _, res = self.simanticize()

            if res is not None:
                return 0, IfElseBlock(if_block.cond, stmts, res)

            # else
            return 0, None

        elif isinstance(self.cur_node, ElseBlock):
            else_block = self.cur_node

            stmts = []

            for stm in else_block.body:

                self.cur_node = stm
                _, res = self.simanticize()

                if res is not None:
                    stmts.append(res)
                else:
                    return 0, None

            return 0, ElseBlock(stmts)

        elif isinstance(self.cur_node, DefaultBlock):
            return 0, self.cur_node
            
        #end
        return 0, None


    def align_type(self, lhs, rhs, exp_type):
        if exp_type:
            return exp_type, lhs, rhs

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

                return "double", lhs, rhs
                                
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

                return "float", lhs, rhs

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

                return "int", lhs, rhs

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

                return "short", lhs, rhs

            if "char" in (lhs.llvm_type, rhs.llvm_type):
                #this is different because of optimization
                if lhs == "bool":
                    lhs.llvm_type = IntType(1)
                    lhs = CastIntHigh(lhs, IntType(8))

                if rhs == "bool":
                    rhs.llvm_type = IntType(1)
                    rhs = CastIntHigh(rhs, IntType(8))

                return "char", lhs, rhs

            return "bool", lhs, rhs #every oprand is boolean


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

        elif self.cur_node == "bool":
            self.cur_node.llvm_type = IntType(1)
            current_type = "bool"

        elif self.cur_node == "float":
            self.cur_node.llvm_type = FloatType()
            current_type = "float"

        elif self.cur_node == "double":
            self.cur_node.llvm_type = DoubleType()
            current_type = "double"

        elif self.cur_node != base_str:
            raise Exception(f"unable to cast {self.cur_node}")

        if current_type in cast_types:
            return base_str, cast_types[current_type](
                self.cur_node,
                base_type
            )

        #else
        return base_str, self.cur_node

    #end
#end

        
