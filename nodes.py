from utils import *
from llvmlite.ir import (
    IntType,
    FloatType,
    Constant,
    ArrayType,
    IRBuilder, 
    GlobalVariable,
)

#base class
class Node:
    def __init__(self, value):
        self.value = value #just a place holder
        self.llvm_type = ""


    def codegen(self, ctx) -> Context:
        return ctx


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


    def codegen(self, ctx) -> Context :
        ctx.suc_value = ctx.builder.neg(
            self.value.codegen(ctx).suc_value
        )

        return ctx

    def __repr__(self):
        return f"Neg({self.value})"


class PosNode(Node):
    def __init__(self, value):
        self.value = value #the actual value, node
        self.llvm_type = value.llvm_type

    def codegen(self, ctx) -> Context:
        ctx.suc_value = self.value
        return ctx

    def __repr__(self):
        return f"PosNode({self.value})"


class ConstantNode(Node):
    def __init__(self, value: int | float , _type = None):
        self.value = value #the constant number
        self.llvm_type = _type #the IR type, a type instance

    def __repr__(self):
        return f"Const({self.value}=>{self.llvm_type})"


    def codegen(self, ctx) -> Context:
        ctx.suc_value = Constant(self.llvm_type, self.value)

        return ctx

class StringNode(Node):
    def __init__(self, value):
        self.value = value
        self.llvm_type = "string"

    def __repr__(self):
        return f"Str({self.value})"

    def codegen(self, ctx: Context) -> Context:
        self.value += '\0'
        #ensuring the null terminator

        zero = Constant(IntType(32), 0)
        
        str_name = name_generator()
        str_type = ArrayType(IntType(8), len(self.value))
        global_str = GlobalVariable(ctx.module, str_type,  next(str_name))

        global_str.global_constant = True
        global_str.initializer = Constant(str_type, bytearray(self.value, "utf-8"))
        
        global_str.linkage = 'private'
        ctx.suc_value = ctx.builder.gep(global_str, [zero, zero])

        return ctx

class BinOpNode(Node):
    def __init__(self, value, lhs, rhs):
        self.value = value #the sign
        self.lhs = lhs #left hand side, node instance
        self.rhs = rhs #right hand side, node instance
        self.llvm_type = "" #the type, auto assign by symanticizer

    def __repr__(self):
        return f"BinOp({self.lhs} {self.value} {self.rhs})"


    def codegen(self, ctx) -> Context:
        ls = self.lhs.codegen(ctx).suc_value
        rs = self.rhs.codegen(ctx).suc_value

        if isinstance(self.llvm_type, IntType):
            if self.value == T_ADD:
                ctx.suc_value = ctx.builder.add(ls, rs)
                return ctx

            elif self.value == T_SUB:
                ctx.suc_value = ctx.builder.sub(ls, rs)
                return ctx

            elif self.value == T_MUL:
                ctx.suc_value = ctx.builder.mul(ls, rs)
                return ctx

            elif self.value == T_DIV:
                ctx.suc_value = ctx.builder.sdiv(ls, rs)
                return ctx

            raise Exception("not a valid operation")

        #these all returns from the function
        #if self.llvm_type is not IntType
        #then it will come here

        if self.value == T_ADD:
            ctx.suc_value = ctx.builder.fadd(ls, rs)
            return ctx

        elif self.value == T_SUB:
            ctx.suc_value = ctx.builder.fsub(ls, rs)
            return ctx

        elif self.value == T_MUL:
            ctx.suc_value = ctx.builder.fmul(ls, rs)
            return ctx
            
        elif self.value == T_DIV:
            ctx.suc_value = ctx.builder.fdiv(ls, rs)
            return ctx

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

    def codegen(self, ctx) -> Context:
        ls = self.lhs.codegen(ctx).suc_value
        rs = self.rhs.codegen(ctx).suc_value

        if self.mean_type not in ("double", "float"):

            if self.value == T_EQS:
                ctx.suc_value = ctx.builder.icmp_signed('==', ls, rs)
                return ctx

            elif self.value == T_NEQ:
                ctx.suc_value = ctx.builder.icmp_signed('!=', ls, rs)
                return ctx

            elif self.value == T_LT:
                ctx.suc_value = ctx.builder.icmp_signed('<', ls, rs)
                return ctx

            elif self.value == T_LTE:
                ctx.suc_value = ctx.builder.icmp_signed('<=', ls, rs)
                return ctx

            elif self.value == T_GT:
                ctx.suc_value = ctx.builder.icmp_signed('>', ls, rs)
                return ctx

            elif self.value == T_GTE:
                ctx.suc_value = ctx.builder.icmp_signed('>=', ls, rs)
                return ctx

            raise Exception("not a valid operation")


        if self.value == T_EQS:
            ctx.suc_value = ctx.builder.fcmp_ordered('==', ls, rs)
            return ctx

        elif self.value == T_NEQ:
            ctx.suc_value = ctx.builder.fcmp_ordered('!=', ls, rs)
            return ctx

        elif self.value == T_LT:
            ctx.suc_value = ctx.builder.fcmp_ordered('<', ls, rs)
            return ctx

        elif self.value == T_LTE:
            ctx.suc_value = ctx.builder.fcmp_ordered('<=', ls, rs)
            return ctx

        elif self.value == T_GT:
            ctx.suc_value = ctx.builder.fcmp_ordered('>', ls, rs)
            return ctx

        elif self.value == T_GTE:
            ctx.suc_value = ctx.builder.fcmp_ordered('>=', ls, rs)
            return ctx

        raise Exception("not a valid operation")



class CastFloToInt(Node):
    def __init__(self, value, casting_type):
        self.value = value # a node subclass
        self.llvm_type = getCurrectType(casting_type)
        self.type = casting_type #the llvm int type, for fexibility


    def codegen(self, ctx) -> Context:
        ctx.suc_value = ctx.builder.fptosi(
            self.value.codegen(ctx).suc_value,
            self.type
        )

        return ctx


    def __repr__(self):
        return f"CastFloToInt({self.value})"


class CastIntToFlo(Node):
    def __init__(self, value, casting_type):
        self.value = value # a node subclass
        self.llvm_type = getCurrectType(casting_type)
        self.type = casting_type

    def codegen(self, ctx) -> Context:
        ctx.suc_value = ctx.builder.sitofp(
            self.value.codegen(ctx).suc_value,
            self.type
        )

        return ctx

    def __repr__(self):
        return f"CastIntToFlo({self.value})"


class CastIntLow(Node):
    def __init__(self, value, casting_type):
        self.value = value
        self.llvm_type = getCurrectType(casting_type)
        self.type = casting_type #the actual llvm type,
        #so we do not have to create more classes

    def codegen(self, ctx) -> Context:
        ctx.suc_value = ctx.builder.trunc(
            self.value.codegen(ctx).suc_value ,
            self.type
        )

        return ctx

    def __repr__(self):
        return f"CastIntLow({self.value} to {self.type})"


class CastIntHigh(Node):
    def __init__(self, value, casting_type):
        self.value = value
        self.llvm_type = getCurrectType(casting_type)
        self.type = casting_type

    def codegen(self, ctx) -> Context:
        ctx.suc_value = ctx.builder.sext(
            self.value.codegen(ctx).suc_value ,
            self.type
        )

        return ctx

    def __repr__(self):
        return f"CastIntHigh({self.value} to {self.type})"

class CastFloLow(Node):
    def __init__(self, value, casting_type):
        self.value = value
        self.llvm_type = getCurrectType(casting_type)
        self.type = casting_type

    def codegen(self, ctx) -> Context:
        ctx.suc_value = ctx.builder.fptrunc(
            self.value.codegen(ctx).suc_value ,
            self.type
        )

        return ctx

    def __repr__(self):
        return f"CastFloLow({self.value} to {self.type})"

class CastFloHigh(Node):
    def __init__(self, value, casting_type):
        self.value = value
        self.llvm_type = getCurrectType(casting_type)
        self.type = casting_type

    def codegen(self, ctx) -> Context :
        ctx.suc_value = ctx.builder.fpext(
            self.value.codegen(ctx).suc_value ,
            self.type
        )

        return ctx

    def __repr__(self):
        return f"CastFloHigh({self.value} to {self.type})"


class VarAssignNode(Node):
    def __init__(self, value, expr, type_):
        self.value = value #the pointer
        self.expr = expr #the expression to be loaded
        self.llvm_type = type_ #the llvm type


    def __repr__(self):
        return f"VarAssign({self.value} = {self.expr})"


    def codegen(self, ctx) -> Context :

        ctx.suc_value = ctx.builder.store(
            self.expr.codegen(ctx).suc_value,
            self.value,
            align=self.value.align
        )

        return ctx


class VarDeclareNode(Node):
    def __init__(self, value,  type_ = 0, var_expr = 0):
        self.value = value #the name
        self.expr = var_expr #the binOpNode
        self.llvm_type = type_ #the type


    def codegen(self, ctx) -> Context:

        ptr = ctx.builder.alloca(
            self.llvm_type,
            name=self.value
        )

        ctx.variables_ptr[self.value] = {
            "type": getCurrectType(self.llvm_type),
            "value": ptr
        }

        varAssNode = VarAssignNode(ptr, self.expr, "")

        ctx = varAssNode.codegen(ctx)

        ctx.suc_value = ptr

        return ctx


    def __repr__(self):
        return f"let {self.value}:{self.llvm_type} = {self.expr}"



class VarFetchNode(Node):
    def __init__(self, value, type_):
        self.value = value #the pointer
        self.llvm_type = type_


    def __repr__(self):
        return f"VarFetch({self.value})"


    def codegen(self, ctx) -> Context:
        ctx.suc_value = ctx.builder.load(self.value, align=self.value.align)
        return ctx


# this starts a new origin
class MyBlock:
    def __init__(self):
        self.body = []

    def __repr__(self):
        return f": {self.body} end"

    def codegen(self, ctx) -> Context:
        pass
    

class DefaultBlock(MyBlock):
    def __init__(self, body: list[Node | DefaultBlock] | None = None):
        self.body = [] if not body else body

    def __repr__(self):
        return f"default : {self.body} end"

    def codegen(self, ctx) -> Context:
        ctx.merge_block = ctx.builder.append_basic_block()
        ctx.builder.branch(ctx.merge_block)

        #replace the builder
        ctx.builder = IRBuilder(ctx.merge_block)
        
        return ctx


class IfElseBlock(MyBlock):
    def __init__(self, cond, body, else_block : DefaultBlock):
        self.cond = cond #a node instance
        self.body = body # list of nodes
        self.else_block = else_block

    def __repr__(self):
        return f"if {self.cond}: {self.body} {self.else_block}"

    def codegen(self, ctx) -> Context:

        # adding nessesary blocks
        then_block = ctx.builder.append_basic_block()
        else_block = ctx.builder.append_basic_block()

        # evaluate condition
        ans = self.cond.codegen(ctx).suc_value

        ctx.builder.cbranch(ans, then_block, else_block)

        # replacing builder
        # building then body
        ctx.builder = IRBuilder(then_block)

        for stmt in self.body:
            ctx = stmt.codegen(ctx)

        then_builder = ctx.builder # preserving the builder

        # replace the builder for else
        ctx.builder = IRBuilder(else_block)

        ctx = self.else_block.codegen(ctx)

        # then jump to merge block
        then_builder.branch(ctx.merge_block)

        return ctx

    #end
#end

class ElseBlock(MyBlock):
    def __init__(self, body: list[Node | DefaultBlock]):
        self.body = body

    def codegen(self, ctx) -> Context:

        ctx.merge_block = ctx.builder.append_basic_block()

        for stmt in self.body:
            ctx = stmt.codegen(ctx)

        # branch
        ctx.builder.branch(ctx.merge_block)

        #replace the builder
        ctx.builder = IRBuilder(ctx.merge_block)
        
        return ctx

    def __repr__(self):
        return f"else: {super().__repr__()}"
