from utils import *


#base class
class Node:
    def __init__(self, value):
        self.value = value #just a place holder

    def codegen(self, builder):
        return None


class NegNode(Node):
    def __init__(self, value):
        self.value = value #the value, node


    def codegen(self, builder):
        return builder.neg(self.value.codegen(builder))

    def __repr__(self):
        return f"Neg({self.value})"


class PosNode(Node):
    def __init__(self, value):
        self.value = value

    def codegen(self, builder):
        return self.value


class ConstantNode(Node):
    def __init__(self, value, llvm_type):
        self.value = value #the constant number
        self.llvm_type = llvm_type #the IR type, a type instance


    def __repr__(self):
        return f"Const({self.value}=>{self.llvm_type})"


    def codegen(self, builder):
        return self.llvm_type(self.value)


class BinOpNode(Node):
    def __init__(self, value, lhs, rhs):
        self.value = value #the sign
        self.lhs = lhs #left hand side, node instance
        self.rhs = rhs #right hand side, node instance

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


class VarDeclareNode(Node):
    def __init__(self, value, type_):
        self.value = value #the name of var
        self.llvm_type = type_ #the llvm IR type

    def __repr__(self):
        return f"let {self.value}:{self.type}"


    def codegen(self, builder):
        ptr = builder.alloca(
            self.llvm_type,
            name=self.value
        )

        ptr.align = self.llvm_type.width // 8

        return ptr
        

class VarAssignNode(Node):
    def __init__(self, value, expr):
        self.value = value #the pointer
        self.expr = expr #the expression to be loaded


    def __repr__(self):
        return f"{self.value} = {self.expr}"


    def codegen(self, builder):
        temp = self.expr.codegen(builder)

        
        builder.store(temp, self.value,
        align=self.value.align)


