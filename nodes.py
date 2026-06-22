from utils import *
from llvmlite.ir import IntType, FloatType, Constant
from llvmlite.ir import IRBuilder

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
        self.llvm_type = "" #the type, auto assign by symanticizer

    def __repr__(self):
        return f"BinOp({self.lhs} {self.value} {self.rhs})"


    def codegen(self, builder):
        ls = self.lhs.codegen(builder)
        rs = self.rhs.codegen(builder)

        if isinstance(self.llvm_type, IntType):
            if self.value == T_ADD:
                return builder.add(ls, rs)

            elif self.value == T_SUB:
                return builder.sub(ls, rs)

            elif self.value == T_MUL:
                return builder.mul(ls, rs)

            elif self.value == T_DIV:
                return builder.sdiv(ls, rs)

            raise Exception("not a valid operation")

        #these all returns from the function
        #if self.llvm_type is not IntType
        #then it will come here

        if self.value == T_ADD:
            return builder.fadd(ls, rs)

        elif self.value == T_SUB:
            return builder.fsub(ls, rs)

        elif self.value == T_MUL:
            return builder.fmul(ls, rs)

        elif self.value == T_DIV:
            return builder.fdiv(ls, rs)

        raise Exception("not a valid operation")


#this ia same as BinOpNode
class CompareNode(Node):
    def __init__(self, value, lhs, rhs):
        self.value = value
        self.lhs = lhs
        self.rhs = rhs
        self.llvm_type = ""
        self.mean_type = "" #this will hold the actual difference

    def __repr__(self):
        return f"CmpNode({self.lhs} {self.value} {self.rhs})"

    def codegen(self, builder):
        ls = self.lhs.codegen(builder)
        rs = self.rhs.codegen(builder)

        if self.mean_type not in ("double", "float"):

            if self.value == T_EQS:
                return builder.icmp_signed('==', ls, rs)

            elif self.value == T_NEQ:
                return builder.icmp_signed('!=', ls, rs)

            elif self.value == T_LT:
                return builder.icmp_signed('<', ls, rs)

            elif self.value == T_LTE:
                return builder.icmp_signed('<=', ls, rs)

            elif self.value == T_GT:
                return builder.icmp_signed('>', ls, rs)

            elif self.value == T_GTE:
                return builder.icmp_signed('>=', ls, rs)

            raise Exception("not a valid operation")


        if self.value == T_EQS:
            return builder.fcmp_ordered('==', ls, rs)

        elif self.value == T_NEQ:
            return builder.fcmp_ordered('!=', ls, rs)

        elif self.value == T_LT:
            return builder.fcmp_ordered('<', ls, rs)

        elif self.value == T_LTE:
            return builder.fcmp_ordered('<=', ls, rs)

        elif self.value == T_GT:
            return builder.fcmp_ordered('>', ls, rs)

        elif self.value == T_GTE:
            return builder.fcmp_ordered('>=', ls, rs)

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

    def __repr__(self):
        return f"CastIntLow({self.value} to {self.type})"


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

    def __repr__(self):
        return f"CastIntHigh({self.value} to {self.type})"

class CastFloLow(Node):
    def __init__(self, value, casting_type):
        self.value = value
        self.llvm_type = getCurrectType(casting_type)
        self.type = casting_type

    def codegen(self, builder):
        return builder.fptrunc(
            self.value.codegen(builder),
            self.type
        )

    def __repr__(self):
        return f"CastFloLow({self.value} to {self.type})"

class CastFloHigh(Node):
    def __init__(self, value, casting_type):
        self.value = value
        self.llvm_type = getCurrectType(casting_type)
        self.type = casting_type

    def codegen(self, builder):
        return builder.fpext(
            self.value.codegen(builder),
            self.type
        )

    def __repr__(self):
        return f"CastFloHigh({self.value} to {self.type})"


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

        return builder


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

        return builder


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


# this starts a new origin

class MyBlock:
    def __init__(self, stmts: list[Node]):
        self.stmts = stmts

    def __repr__(self):
        return f": {self.stmts} end"

    def codegen(self, builder):
        pass


class IfThenBlock(MyBlock):
    def __init__(self, cond, stmts):
        self.cond = cond #a node instance
        self.stmts = stmts # list of nodes

    def __repr__(self):
        return f"if {self.cond} {super().__repr__()}"

    def codegen(self, builder):

        #building the condition
        ans = self.cond.codegen(builder)

        #prebuilding branches
        then_block = builder.append_basic_block()
        merge_block = builder.append_basic_block()

        # branching with the answer
        builder.cbranch(ans, then_block, merge_block)

        then_builder = IRBuilder(then_block)

        for stmt in self.stmts:
            then_builder = stmt.codegen(then_builder)

        then_builder.branch(merge_block)

        return IRBuilder(merge_block)

    #end
#end

