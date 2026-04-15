from utils import *


#base class
class Node:
    def __init__(self, value):
        self.value = value #just a place holder
        self.llvm_type = ""
        

    def codegen(self, builder):
        return None


    def __eq__(self, other):
        if isinstance(other, str):
            return self.llvm_type == other

        return False


    def __ne__(self, other):

        if isinstance(other, str):
            return self.llvm_type != other

        return False


class NegNode(Node):
    def __init__(self, value):
        self.value = value #the value, node
        self.llvm_type = value.llvm_type


    def codegen(self, builder):
        return builder.neg(self.value.codegen(builder))

    def __repr__(self):
        return f"Neg({self.value})"


class PosNode(Node):
    def __init__(self, value):
        self.value = value #the actual value, node
        self.llvm_type = value.llvm_type

    def codegen(self, builder):
        return self.value


class ConstantNode(Node):
    def __init__(self, value, _type = None):
        self.value = value #the constant number
        self.llvm_type = _type #the IR type, a type instance

    def __repr__(self):
        return f"Const({self.value}=>{self.llvm_type})"


    def codegen(self, builder):
        return self.llvm_type(self.value)


class BinOpNode(Node):
    def __init__(self, value, lhs, rhs):
        self.value = value #the sign
        self.lhs = lhs #left hand side, node instance
        self.rhs = rhs #right hand side, node instance
        self.llvm_type = "" #the type, auto assign by parser

    def __repr__(self):
        return f"BinOp({self.lhs} {self.value} {self.rhs})"


    def codegen(self, builder):
        ls = self.lhs.codegen(builder)
        rs = self.rhs.codegen(builder)

        if self.value == T_ADD:
            return builder.add(ls, rs)

        elif self.value == T_SUB:
            return builder.sub(ls, rs)

        elif self.value == T_MUL:
            return builder.mul(ls, rs)

        elif self.value == T_DIV:
            return builder.sdiv(ls, rs)

        else:
            raise Exception("not a valid operation")


class CastFloToInt(Node):
    def __init__(self, value):
        self.value = value # a node subclass
        self.llvm_type = "intiger"


    def codegen(self, builder):
        return builder.fptosi(self.value.codegen(builder))
        

    def __repr__(self):

        return f"CastFloToInt({self.value})"


class CastIntToFlo(Node):
    def __init__(self, value):
        self.value = value # a node subclass
        self.llvm_type = "float"

    def codegen(self, builder):
        return builder.sitofp(self.value.codgen(builder))


    def __repr__(self):
        return f"CastIntToFlo({self.value})"

        

class VarAssignNode(Node):
    def __init__(self, value, expr):
        self.value = value #the pointer
        self.expr = expr #the expression to be loaded


    def __repr__(self):
        return f"VarAssign({self.value} = {self.expr})"


    def codegen(self, builder):
        
        builder.store(
            self.expr.codegen(builder), 
            self.value,
            align=self.value.align
        )
        
        return None


class VarDeclareNode(Node):
    def __init__(self, value,  type_ = 0, var_expr = 0):
        self.value = value #the name
        self.expr = var_expr #the binOpNode
        self.llvm_type = type_ #the type


    def codegen(self, builder):
        ptr = builder.alloca(
            self.llvm_type,
            name=self.value
        )

        ptr.align = self.llvm_type.width // 8
        variables_ptr[self.value] = ptr

        varAssNode = VarAssignNode(ptr, self.expr)

        varAssNode.codegen(builder)
        
        return None


    def __repr__(self):
        return f"let {self.value}:{self.llvm_type} = {self.expr}"


class VarFetchNode(Node):
    def __init__(self, value):
        self.value = value #the pointer


    def __repr__(self):
        return f"VarFetch({self.value})"


    def codegen(self, builder):
        return builder.load(self.value, align=self.value.align)




        


        


