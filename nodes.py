from utils import (
    T_ADD,
    T_SUB,
    T_DIV,
    T_MUL,
    T_MOD,
    T_EQS,
    T_NEQ,
    T_LT,
    T_LTE,
    T_GT,
    T_GTE,
    name_generator,

    Context,
    getCurrectType,
    CodegenError,
    Symbol,
)

from llvmlite.ir import (
    IntType,
    FloatType,
    Constant,
    ArrayType,
    IRBuilder,
    GlobalVariable,
)

from diagnostical import Span
from lexical import Token

#base class
class Node:
    def __init__(self, value, span):
        self.value = value #just a place holder
        self.llvm_type = ""
        self.span = span

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
    def __init__(self, value, span):
        super().__init__(value, span)
        self.llvm_type = value.llvm_type


    def codegen(self, ctx) -> Context :

        llvm_res = self.value.codegen(ctx).suc_value
        llvm_type = getCurrectType(self.llvm_type)

        if llvm_type not in (
            "double", "float",
            "long", "int", "short", "char", "bool"):

            raise CodegenError(f"unknown type {llvm_type} for negation operation")

        elif llvm_type in ("double", "float"):
            ctx.suc_value = ctx.builder.fneg(llvm_res)

        else:
            ctx.suc_value = ctx.builder.neg(llvm_res)

        return ctx

    def __repr__(self):
        return f"Neg({self.value})"

class NotNode(Node):
    def __init__(self, value, span):
        super().__init__(value, span)
        self.llvm_type = value.llvm_type

    def __repr__(self):
        return f"Not({self.value})"

    def codegen(self, ctx) -> Context:
        ctx.suc_value = ctx.builder.not_(
            self.value.codegen(ctx).suc_value
        )

        return ctx

class ConstantNode(Node):
    def __init__(self, value: int | float, span: Span,  _type = None):
        super().__init__(value, span) # value : the constant number
        self.llvm_type = _type #the IR type, a type instance

    def __repr__(self):
        return f"Const({self.value}=>{self.llvm_type})"


    def codegen(self, ctx) -> Context:
        ctx.suc_value = Constant(self.llvm_type, self.value)

        return ctx

class BitNode(Node):
    def __init__(self, value: bool, span: Span):
        super().__init__(value, span)
        self.llvm_type = "bool"

    def __repr__(self):
        return f"Bit({self.value})"

    def codegen(self, ctx) -> Context:
        ctx.suc_value = Constant(self.llvm_type, self.value)

        return ctx

class StringNode(Node):
    def __init__(self, value: str, span: Span):
        super().__init__(value, span)
        self.llvm_type = "string"

    def __repr__(self):
        return f"Str({self.value})"

    def codegen(self, ctx: Context) -> Context:
        self.value += '\0'
        #ensuring the null terminator
        
        zero = Constant(IntType(32), 0)

        str_name = name_generator()
        str_type = ArrayType(IntType(8), len(self.value))
        global_str = GlobalVariable(ctx.module, str_type, str_name)

        global_str.global_constant = True
        global_str.initializer = Constant(str_type, bytearray(self.value, "utf-8"))

        global_str.linkage = 'private'
        ctx.suc_value = ctx.builder.gep(global_str, [zero, zero])

        return ctx

class BinOpNode(Node):
    def __init__(self, value: Token, lhs: Node, rhs: Node, span: Span):
        super().__init__(value, span)
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

            elif self.value == T_SUB:
                ctx.suc_value = ctx.builder.sub(ls, rs)

            elif self.value == T_MUL:
                ctx.suc_value = ctx.builder.mul(ls, rs)

            elif self.value == T_DIV:
                ctx.suc_value = ctx.builder.sdiv(ls, rs)

            elif self.value == T_MOD:
                ctx.suc_value = ctx.builder.srem(ls, rs)

            else:
                raise CodegenError("not a valid operation")

            return ctx

        #these all returns from the function
        #if self.llvm_type is not IntType
        #then it will come here

        if self.value == T_ADD:
            ctx.suc_value = ctx.builder.fadd(ls, rs)

        elif self.value == T_SUB:
            ctx.suc_value = ctx.builder.fsub(ls, rs)

        elif self.value == T_MUL:
            ctx.suc_value = ctx.builder.fmul(ls, rs)

        elif self.value == T_DIV:
            ctx.suc_value = ctx.builder.fdiv(ls, rs)

        elif self.value == T_MOD:
            ctx.suc_value = ctx.builder.frem(ls, rs)

        else:
            raise CodegenError("not a valid operation")

        return ctx


#this ia same as BinOpNode
class CompareNode(Node):
    def __init__(self, value: Token, lhs: Node, rhs: Node, span: Span):
        super().__init__(value, span)
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

            elif self.value == T_NEQ:
                ctx.suc_value = ctx.builder.icmp_signed('!=', ls, rs)

            elif self.value == T_LT:
                ctx.suc_value = ctx.builder.icmp_signed('<', ls, rs)

            elif self.value == T_LTE:
                ctx.suc_value = ctx.builder.icmp_signed('<=', ls, rs)

            elif self.value == T_GT:
                ctx.suc_value = ctx.builder.icmp_signed('>', ls, rs)

            elif self.value == T_GTE:
                ctx.suc_value = ctx.builder.icmp_signed('>=', ls, rs)

            else:
                raise CodegenError(f"not a valid operation {self.value}")

            return ctx


        if self.value == T_EQS:
            ctx.suc_value = ctx.builder.fcmp_ordered('==', ls, rs)

        elif self.value == T_NEQ:
            ctx.suc_value = ctx.builder.fcmp_ordered('!=', ls, rs)

        elif self.value == T_LT:
            ctx.suc_value = ctx.builder.fcmp_ordered('<', ls, rs)

        elif self.value == T_LTE:
            ctx.suc_value = ctx.builder.fcmp_ordered('<=', ls, rs)

        elif self.value == T_GT:
            ctx.suc_value = ctx.builder.fcmp_ordered('>', ls, rs)

        elif self.value == T_GTE:
            ctx.suc_value = ctx.builder.fcmp_ordered('>=', ls, rs)

        else:
            raise CodegenError(f"not a valid operation {self.value}")

        return ctx

class BitOpNode(Node):
    def __init__(self, value: str, lhs: Node, rhs: Node, span: Span):
        super().__init__(value, span)
        self.lhs = lhs
        self.rhs = rhs
        self.llvm_type = ""

    def __repr__(self):
        return f"BitOpNode({self.lhs} {self.value} {self.rhs})"

    def codegen(self, ctx) -> Context:

        ls = self.lhs.codegen(ctx).suc_value
        rs = self.rhs.codegen(ctx).suc_value

        if self.value == "and":
            ctx.suc_value = ctx.builder.and_(ls, rs)

        elif self.value == "or":
            ctx.suc_value = ctx.builder.or_(ls, rs)

        else:
            raise CodegenError(f"not a valid operation {self.value}")

        return ctx

class CastFloToInt(Node):
    def __init__(self, value: Node, casting_type, span: Span):
        super().__init__(value, span)
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
    def __init__(self, value: Node, casting_typ,  span: Span):
        super().__init__(value, span)
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
    def __init__(self, value: Node, casting_type, span: Span):
        super().__init__(value, span)
        self.llvm_type = getCurrectType(casting_type)
        self.type = casting_type # the actual llvm type

    def codegen(self, ctx) -> Context:
        ctx.suc_value = ctx.builder.trunc(
            self.value.codegen(ctx).suc_value ,
            self.type
        )

        return ctx

    def __repr__(self):
        return f"CastIntLow({self.value} to {self.type})"


class CastIntHigh(Node):
    def __init__(self, value: Node, casting_type, span: Span):
        super().__init__(value, span)
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
    def __init__(self, value: Node, casting_type, span: Span):
        super().__init__(value, span)
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
    def __init__(self, value: Node, casting_type, span: Span):
        super().__init__(value, span)
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
    def __init__(self, value: Symbol, expr: Node, span: Span):
        super().__init__(value, span)
        self.expr = expr #the expression to be loaded
        self.llvm_type = ""

    def __repr__(self):
        return f"VarAssign({self.value}:{self.llvm_type} = {self.expr})"

    def codegen(self, ctx) -> Context :

        ctx.suc_value = ctx.builder.store(
            self.expr.codegen(ctx).suc_value,
            self.value.ptr,
            align=self.value.ptr.align
        )

        return ctx


class VarDeclareNode(Node):
    def __init__(self, value: Symbol, span: Span, type_ = 0, var_expr = 0):
        super().__init__(value, span)
        self.expr = var_expr #the expression
        self.llvm_type = type_ #the type, temporary

    def codegen(self, ctx) -> Context:

        self.value.ptr = ctx.builder.alloca(
            self.value.llvm_type,
            name=self.value.name
        )

        self.value.llvm_type = getCurrectType(self.value.llvm_type)

        varAssNode = VarAssignNode(self.value, self.expr)

        ctx = varAssNode.codegen(ctx)
        ctx.suc_value = self.value.ptr

        return ctx

    def __repr__(self):
        return f"let {self.value}:{self.llvm_type} = {self.expr}"

class VarFetchNode(Node):
    def __init__(self, value: Symbol, span: Span):
        super().__init__(value, span)
        self.llvm_type = "" #the type, temporary

    def __repr__(self):
        return f"VarFetch({self.value}:{self.llvm_type})"

    def codegen(self, ctx) -> Context:
        ctx.suc_value = ctx.builder.load(
            self.value.ptr,
            align=self.value.ptr.align
        )

        return ctx

class CallNode(Node):
    def __init__(self, value, params: list[Node], span: Span):
        # value: the name, later the ptr
        super().__init__(value, span)
        self.params = params # the paramiters
        self.llvm_type = "" # the return type, str

    def __repr__(self):
        return f"Call:{self.value}({self.params})->{self.llvm_type}"

    def codegen(self, ctx):
        # eval params
        params = []

        for p in self.params:
            params.append(p.codegen(ctx).suc_value)

        ctx.suc_value = ctx.builder.call(self.value, params)

        return ctx

class BreakNode(Node):

    def __init__(self):
        self.value = None

    def __repr__(self):
        return "break"

    def __eq__(self, other):
        return other == "break"

    def __ne__(self, other):
        return other != "break"

    def codegen(self, ctx):

        if not ctx.cond_block:
            raise CodegenError("break statement without any loop!")

        ctx.should_stop = True
        ctx.builder.branch(ctx.merge_block) # dead

        return ctx

class ContinueNode(Node):

    def __init__(self):
        self.value = None

    def __repr__(self):
        return "continue"

    def __eq__(self, other):
        return "continue" == other

    def __ne__(self, other):
        return "continue" != other

    def codegen(self, ctx):

        if not ctx.cond_block:
            raise CodegenError("continue statement without any loop!")

        ctx.should_stop = True
        ctx.builder.branch(ctx.cond_block) # dead
        
        return ctx

# this starts a new origin
class DefaultBlock:
    def __init__(self):
        self.body = []

    def __repr__(self):
        return "{" + repr(self.body) + "}"

    def codegen(self, ctx) -> Context:

        # first priority
        if ctx.if_merge_block:
            ctx.builder.branch(ctx.if_merge_block)

        elif ctx.merge_block:
            ctx.builder.branch(ctx.merge_block)

        else:
            raise CodegenError("we do not have any merge block to jump")

        return ctx


class IfElseBlock(DefaultBlock):
    def __init__(self, cond: Node, body: list[Node | DefaultBlock], else_block : DefaultBlock, span: Span):
        self.cond = cond # a node instance
        self.body = body # a list of nodes
        self.else_block = else_block # the else block
        self.span = span # the span

    def __repr__(self):
        return ("if " + repr(self.cond) +
            " { " + repr(self.body) + "\n} else " +
            repr(self.else_block))

    def codegen(self, ctx) -> Context:

        # adding nessesary blocks
        then_block = ctx.builder.append_basic_block()
        else_block = ctx.builder.append_basic_block()
        if not ctx.if_merge_block:
            ctx.if_merge_block = ctx.builder.append_basic_block()

        # evaluate condition
        ans = self.cond.codegen(ctx).suc_value

        ctx.builder.cbranch(ans, then_block, else_block)

        # replacing builder
        # building then body
        ctx.builder = IRBuilder(then_block)

        # reserving
        merg = ctx.if_merge_block
        ctx.if_merge_block = None

        for stmt in self.body:
            ctx = stmt.codegen(ctx)
            if ctx.should_stop: break

        # restoring
        ctx.if_merge_block = merg

        # jumping to the merge block if there is not break or continue
        if not ctx.should_stop:
            ctx.builder.branch(ctx.if_merge_block)

        ctx.should_stop = False

        # replace the builder for else
        ctx.builder = IRBuilder(else_block)
        ctx = self.else_block.codegen(ctx)

        # replace the builder for merge block
        ctx.builder = IRBuilder(ctx.if_merge_block)

        return ctx

    #end
#end

class ElseBlock(DefaultBlock):
    def __init__(self, body: list[Node | DefaultBlock], span: Span):
        self.body = body
        self.span = span

    def codegen(self, ctx) -> Context:

        for stmt in self.body:
            ctx = stmt.codegen(ctx)
            if ctx.should_stop: break

        # we have already branched, so return
        if ctx.should_stop:
            ctx.should_stop = False
            return ctx

        # we haven't branched yet
        if ctx.if_merge_block:
            ctx.builder.branch(ctx.if_merge_block)

        elif ctx.merge_block:
            ctx.builder.branch(ctx.merge_block)

        else:
            raise CodegenError("we do not have any merge block to jump")

        return ctx

    def __repr__(self):
        return super().__repr__()

class WhileBlock(DefaultBlock):
    def __init__(self, cond, body, else_block, span):
        self.cond = cond
        self.body = body
        self.else_block = else_block
        self.span = span

    def __repr__(self):
        return ("while " + repr(self.cond) + " {"+
            repr(self.body) + "\n} else "+
            repr(self.else_block))

    def codegen(self, ctx):

        cond_block = ctx.builder.append_basic_block()
        body_block = ctx.builder.append_basic_block()
        else_block = ctx.builder.append_basic_block()
        merge_block = ctx.builder.append_basic_block()

        # eval condition
        ctx.builder.branch(cond_block) # this builder is dead
        ctx.builder = IRBuilder(cond_block)
        ans = self.cond.codegen(ctx).suc_value

        # now branching according to result
        ctx.builder.cbranch(ans, body_block, else_block) # dead
        ctx.builder = IRBuilder(body_block)

        # some preseving before body eval
        pre_cond_block = ctx.cond_block
        pre_merge_block = ctx.merge_block

        # loading this loop's config
        ctx.cond_block = cond_block
        ctx.merge_block = merge_block

        # eval body
        for stmt in self.body:
            ctx = stmt.codegen(ctx)
            if ctx.should_stop: break

        # because we have aleady branched
        if not ctx.should_stop:
            ctx.builder.branch(cond_block)

        # setting up
        ctx.merge_block = merge_block
        ctx.should_stop = False
        ctx.if_merge_block = None # the child if should be over, logicall

        ctx.builder = IRBuilder(else_block)
        ctx = self.else_block.codegen(ctx)

        ctx.builder = IRBuilder(ctx.merge_block)
        
        # restoring the previous stuffs
        ctx.cond_block = pre_cond_block
        ctx.merge_block = pre_merge_block

        return ctx
