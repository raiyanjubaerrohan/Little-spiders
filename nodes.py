from utils import *
from llvmlite.ir import IntType, FloatType, Constant

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

    def __repr__(self):
        return f"PosNode({self.value})"


class ConstantNode(Node):
    def __init__(self, value, _type = None):
        self.value = value #the constant number
        self.llvm_type = _type #the IR type, a type instance

    def __repr__(self):
        return f"Const({self.value}=>{self.llvm_type})"


    def codegen(self, builder):
        return Constant(self.llvm_type, self.value)




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
            if isinstance(
                self.llvm_type,
                IntType
            ):
                return builder.add(ls, rs)

            else:
                return builder.fadd(ls, rs)

        elif self.value == T_SUB:
            if isinstance(
                self.llvm_type,
                IntType
            ):
                return builder.sub(ls, rs)

            else:
                return builder.fsub(ls, rs)

        elif self.value == T_MUL:
            if isinstance(
                self.llvm_type,
                IntType
            ):
                return builder.mul(ls, rs)

            else:
                return builder.fmul(ls, rs)

        elif self.value == T_DIV:
            if isinstance(
                self.llvm_type,
                IntType
            ):
                return builder.sdiv(ls, rs)

            else:
                return builder.fdiv(ls, rs)

        else:
            raise Exception("not a valid operation")
    

class CastFloToInt(Node):
    def __init__(self, value, casting_type):
        self.value = value # a node subclass
        self.llvm_type = getCurrectType(casting_type)
        self.type = casting_type #the llvm int type, for fexibility


    def codegen(self, builder):
        return builder.fptosi(
            self.value.codegen(builder),
            self.type
        )
    

    def __repr__(self):
        return f"CastFloToInt({self.value})"


class CastIntToFlo(Node):
    def __init__(self, value, casting_type):
        self.value = value # a node subclass
        self.llvm_type = getCurrectType(casting_type)
        self.type = casting_type

    def codegen(self, builder):
        return builder.sitofp(
            self.value.codegen(builder),
            self.type
        )

    def __repr__(self):
        return f"CastIntToFlo({self.value})"


class CastIntLow(Node):
    def __init__(self, value, casting_type):
        self.value = value
        self.llvm_type = getCurrectType(casting_type)
        self.type = casting_type #the actual llvm type,
        #so we do not have to create more classes

    def codegen(self, builder):
        return builder.trunc(
            self.value.codegen(builder),
            self.type
        )


class CastIntHigh(Node):
    def __init__(self, value, casting_type):
        self.value = value
        self.llvm_type = getCurrectType(casting_type)
        self.type = casting_type

    def codegen(self, builder):
        return builder.sext(
            self.value.codegen(builder),
            self.type
        )


class VarAssignNode(Node):
    def __init__(self, value, expr, type_):
        self.value = value #the pointer
        self.expr = expr #the expression to be loaded
        self.llvm_type = type_ #the llvm type


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

        variables_ptr[self.value] = {
            "type": getCurrectType(self.llvm_type),
            "value": ptr
        }

        varAssNode = VarAssignNode(ptr, self.expr, "")

        varAssNode.codegen(builder)
        
        return True


    def __repr__(self):
        return f"let {self.value}:{self.llvm_type} = {self.expr}"



class VarFetchNode(Node):
    def __init__(self, value, type_):
        self.value = value #the pointer
        self.llvm_type = type_


    def __repr__(self):
        return f"VarFetch({self.value})"


    def codegen(self, builder):
        return builder.load(self.value, align=self.value.align)




        


        


