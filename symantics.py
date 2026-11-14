from nodes import (
    Node,
    VarAssignNode,
    VarDeclareNode,
    VarFetchNode,
    BinOpNode,
    BitOpNode,
    CompareNode,
    ConstantNode,
    BitNode,
    NegNode,
    NotNode,
    StringNode,
    BreakNode,
    ContinueNode,
    IfElseBlock,
    WhileBlock,
    ElseBlock,
    CallNode,
    DefaultBlock,
    CastIntToFlo,
    CastFloToInt,
    CastIntHigh,
    CastIntLow,
    CastFloHigh,
    CastFloLow,
)

from llvmlite.ir import (
	FloatType,
	IntType,
	DoubleType,
	PointerType,
)

from diagnostical import Diagnostics
from utils import T_POISON, Symbol

type_casting = {
    "double": {
        "float": CastFloHigh,
        "long": CastIntToFlo,
        "int": CastIntToFlo,
        "short": CastIntToFlo,
        "char": CastIntToFlo,
        "bool": CastIntToFlo
    },

    "float": {
        "double": CastFloLow,
        "long": CastIntToFlo,
        "int": CastIntToFlo,
        "short": CastIntToFlo,
        "char": CastIntToFlo,
        "bool": CastIntToFlo
    },

    "long": {
        "double": CastFloToInt,
        "float": CastFloToInt,
        "int": CastIntHigh,
        "short": CastIntHigh,
        "char": CastIntHigh,
        "bool": CastIntHigh
    },

    "int": {
        "double": CastFloToInt,
        "float": CastFloToInt,
        "long": CastIntLow,
        "short": CastIntHigh,
        "char": CastIntHigh,
        "bool": CastIntHigh
    },

    "short": {
        "double": CastFloToInt,
        "float": CastFloToInt,
        "long": CastIntLow,
        "int": CastIntLow,
        "char": CastIntHigh,
        "bool": CastIntHigh
    },

    "char": {
        "double": CastFloToInt,
        "float": CastFloToInt,
        "long": CastIntLow,
        "int": CastIntLow,
        "short": CastIntLow,
        "bool": CastIntHigh
    }
}


class Symanticizer:

    def __init__(self, diagctx):
        self.cur_node = None
        self.exp_type = None
        self.diagctx = diagctx

    def load(self, ast) -> None:
        self.cur_node = ast

    def simanticize_varDecNode(self) -> VarDeclareNode | str:
        varDec = self.cur_node
        self.cur_node = varDec.expr
        self.exp_type = varDec.value.llvm_type

        expr = self.simanticize()

        self.cur_node = expr
        comp_res = self.make_compatible(varDec.value.llvm_type, expr.llvm_type)

        # return a fresh one
        newVarDec =  VarDeclareNode(
            varDec.value,
            varDec.span,
            comp_res.llvm_type,
            comp_res
        )
        newVarDec.value.llvm_type = comp_res.llvm_type

        return newVarDec

    def simanticize_varAssNode(self) -> VarAssignNode | str:

        node = self.cur_node

        self.exp_type = node.value.llvm_type
        self.cur_node = node.expr
        expr = self.simanticize()

        self.cur_node = expr
        comp_res = self.make_compatible(
            node.value.llvm_type, expr.llvm_type
        )

        # I do not need the right type,
        # because I have one in
        # node.value.llvm_type

        return VarAssignNode(node.value, comp_res, node.span)

    def simanticize_opNode(self):

        tree = self.cur_node
        optype = type(tree) # I am using some python hacks

        ### lhs
        self.cur_node = tree.lhs
        res_lhs = self.simanticize()
        if self.exp_type == "string":
            self.diagctx.emit(Diagnostics(
                "we can not do any operation with strings, but you have somehow put a operation after it.",
                "S0389",
                tree.span,
                smsg="remove this string with another data type"
            ))
            return T_POISON

        ### rhs
        self.cur_node = tree.rhs
        res_rhs = self.simanticize()
        if self.exp_type == "string":
            self.diagctx.emit(Diagnostics(
                "we can not do any operation with strings, but you have somehow put a operation before it.",
                "S0389",
                tree.span,
                smsg="remove this string with another data type"
            ))
            return T_POISON

        ty_lhs, ty_rhs = self.align_type(
            res_lhs,
            res_rhs
        )
        #this will set self.exp_type automatically

        opNode = optype(tree.value, ty_lhs, ty_rhs, tree.span)
        opNode.llvm_type = self.exp_type

        return opNode


    def simanticize_compareNode(self):

        tree = self.cur_node

        ### lhs
        self.cur_node = tree.lhs
        res_lhs = self.simanticize()
        if self.exp_type == "string":
            self.diagctx.emit(Diagnostics(
                "we can not do any operation with strings, but you have somehow put a operation after it.",
                "S0389",
                tree.span,
                smsg="remove this string with another data type"
            ))
            return T_POISON

        ### rhs
        self.cur_node = tree.rhs
        res_rhs = self.simanticize()
        if self.exp_type == "string":
            self.diagctx.emit(Diagnostics(
                "we can not do any operation with strings, but you have somehow put a operation after it.",
                "S0389",
                tree.span,
                smsg="remove this string with another data type"
            ))
            return T_POISON

        ty_lhs, ty_rhs = self.align_type(
            res_lhs,
            res_rhs
        )
        # this will set self.exp_type automatically

        cmpNode = CompareNode(tree.value, ty_lhs, ty_rhs, tree.span)

        cmpNode.llvm_type = "bool"
        cmpNode.mean_type = self.exp_type

        self.exp_type = "bool"

        return cmpNode, None

    def simanticize(self) -> Node | str:

        if self.cur_node == T_POISON:
            return T_POISON

        if isinstance(self.cur_node, VarDeclareNode):
            return self.simanticize_varDecNode()

        elif isinstance(self.cur_node, VarAssignNode):
            return self.simanticize_varAssNode()

        elif isinstance(self.cur_node, (BinOpNode, BitOpNode)):
            return self.simanticize_opNode()

        elif isinstance(self.cur_node, CompareNode):
            return self.simanticize_compareNode()

        elif isinstance(self.cur_node, (ConstantNode, BitNode)):
            self.exp_type = self.cur_node.llvm_type
            return self.cur_node

        elif isinstance(self.cur_node, VarFetchNode):
            self.exp_type = self.cur_node.value.llvm_type
            self.cur_node.llvm_type = self.exp_type
            
            return self.cur_node

        elif isinstance(self.cur_node, (NegNode, NotNode)):
            node = self.cur_node

            self.cur_node = node.value
            res_node = self.simanticize()
            right_type = self.get_currect_type()

            # new node, fresh one
            newNode = type(node)(res_node, node.span)
            newNode.llvm_type = res_node.llvm_type

            # set the llvm_type of value
            newNode.value.llvm_type = right_type

            return newNode

        elif isinstance(self.cur_node, StringNode):
            self.exp_type = "string"
            return self.cur_node

        elif isinstance(self.cur_node, CallNode):
            return self.simanticize_callNode()

        elif isinstance(self.cur_node, (BreakNode, ContinueNode)):
            return self.cur_node

        elif isinstance(self.cur_node, IfElseBlock):
            return self.simanticize_if_elseBlock()

        elif isinstance(self.cur_node, ElseBlock):
            return self.simanticize_elseBlock()

        elif isinstance(self.cur_node, WhileBlock):
            return self.simanticize_whileBlock()

        elif isinstance(self.cur_node, DefaultBlock):
            return self.cur_node

        self.diagctx.emit(Diagnostics(
            "internal error: {type(self.cur_node)} did not match any type of the list",
            "E0003",
            self.cur_node.span,
            _help="if you are developer, please check it yourself."
        ))
        
        return T_POISON

    def simanticize_callNode(self) -> CallNode | str:
        node = self.cur_node

        # for the params
        if not node.llvm_type["var_arg"]:
            g_params = len(node.params)
            e_params = len(node.llvm_type["params_type"])

            if g_params != e_params:
                self.diagctx.emit(Diagnostics(
                    f"the function {node.name} takes {e_params} arg(s)"   # it is the
                    f"but you have passed {g_params} arg(s)",             # main msg
                    "S0579",
                    node.span
                ))
                return T_POISON
            #else

            typed_params = []
            for n in range(g_params): # or e_params
                self.exp_type = node.llvm_type["params_type"][n]
                self.cur_node = node.params[n]

                res = self.simanticize()
                if res == T_POISON: return T_POISON

                self.cur_node = res
                comp_res = self.make_compatible(
                    node.llvm_type["params_type"][n],
                    res.llvm_type
                )

                typed_params.append(comp_res)

            callNode = CallNode(node.value, typed_params, node.span)
            callNode.llvm_type = node.llvm_type["ret_type"]

            self.exp_type = callNode.llvm_type

            return callNode

        #else
        g_params = len(node.params)
        e_params = len(node.llvm_type["params_type"])

        if g_params < e_params: # the opposite case
            self.diagctx.emit(Diagnostics(
                f"the function {node.name} takes {e_params} arg(s)" # it is the
                f"but you have passed {g_params} arg(s)",           # main msg
                "S0579",
                node.span
            ))
            return T_POISON

        typed_params = []
        n = 0

        while n < e_params:
            self.cur_node = node.params[n]
            self.exp_type = node.llvm_type["params_type"][n]

            # simanticize
            res = self.simanticize()
            if res == T_POISON: return T_POISON

            # make compatible
            self.cur_node = res
            comp_res = self.make_compatible(
                node.llvm_type["params_type"][n],
                res.llvm_type
            )

            typed_params.append(comp_res)

            n += 1

        while n < g_params:
            self.cur_node = node.params[n]
            self.exp_type = ""

            # simanticize
            res = self.simanticize()
            if res == T_POISON: return T_POISON

            # get llvm type
            self.exp_type = res.llvm_type
            llvm_type = self.get_currect_type()

            res.llvm_type = llvm_type

            typed_params.append(res)

            n += 1

        callNode = CallNode(node.value, typed_params, node.span)
        callNode.llvm_type = node.llvm_type["ret_type"]

        self.exp_type = callNode.llvm_type

        return callNode

    def simanticize_if_elseBlock(self) -> IfElseBlock | str:

        if_block = self.cur_node

        # the condition
        self.cur_node = if_block.cond
        res_cond = self.simanticize()
        if res_cond == T_POISON: return T_POISON

        res_cond.llvm_type = IntType(1)

        # the body
        stmts = []

        for stmt in if_block.body:
            self.cur_node = stmt
            res = self.simanticize()

            stmts.append(res)

        # the else block
        self.cur_node = if_block.else_block
        res_else_block = self.simanticize()

        return IfElseBlock(res_cond, stmts, res_else_block, if_block.span)

    def simanticize_whileBlock(self) -> WhileBlock | str:

        while_block = self.cur_node

        # the condition
        self.cur_node = while_block.cond
        res_cond = self.simanticize()
        if res_cond == T_POISON: return T_POISON

        res_cond.llvm_type = IntType(1)

        # the body
        stmts = []
        for stmt in while_block.body:
            self.cur_node = stmt
            res = self.simanticize()

            stmts.append(res)

        # the else block
        self.cur_node = while_block.else_block
        res_else_block = self.simanticize()

        return WhileBlock(res_cond, stmts, res_else_block, while_block.span)

    def simanticize_elseBlock(self) -> ElseBlock:

        else_block = self.cur_node

        stmts = []

        for stm in else_block.body:
            self.cur_node = stm
            res = self.simanticize()

            stmts.append(res)

        return ElseBlock(stmts, else_block.span)

    def get_currect_type(self) -> IntType | DoubleType | FloatType | PointerType | None:
        if self.exp_type == "long":
            return IntType(64)

        if self.exp_type == "int":
            return IntType(32)

        if self.exp_type == "short":
            return IntType(16)

        if self.exp_type == "char":
            return IntType(8)

        if self.exp_type == "bool":
            return IntType(1)

        if self.exp_type == "double":
            return DoubleType()

        if self.exp_type == "float":
            return FloatType()

        if self.exp_type == "string":
            return IntType(8).as_pointer()

        self.diagctx.emit(Diagnostics(
            f"the type {self.exp_type} did not match any type in the list.",
            "S0689",
            self.cur_node.span
        ))

    def align_type(self, lhs, rhs) -> tuple[Node, Node]:

        if "double" in (lhs.llvm_type, rhs.llvm_type):
            # means lhs or rhs is "double"

            temp = self.cur_node
            #temporary var to store the current node

            self.cur_node = lhs #for passing in select_type
            lhs = self.select_type(
                DoubleType(),
                "double",
                **type_casting["double"]
            )

            self.cur_node = rhs
            rhs = self.select_type(
                DoubleType(),
                "double",
                **type_casting["double"]
            )

            #at very end reassign the current node to be currect
            self.cur_node = temp
            self.exp_type = "double"

            return lhs, rhs

        if "float" in (lhs.llvm_type, rhs.llvm_type):

            #same as upper check
            temp = self.cur_node

            self.cur_node = lhs
            lhs = self.select_type(
                FloatType(),
                "float",
                **type_casting["float"]
            )

            self.cur_node = rhs
            rhs = self.select_type(
                FloatType(),
                "float",
                **type_casting["float"]
            )

            self.cur_node = temp
            self.exp_type = "float"

            return lhs, rhs

        if "long" in (lhs.llvm_type, rhs.llvm_type):
            temp = self.cur_node

            self.cur_node = lhs
            lhs = self.select_type(
                IntType(64),
                "long",
                **type_casting["long"]
            )

            self.cur_node = rhs
            rhs = self.select_type(
                IntType(64),
                "long",
                **type_casting["long"]
            )

            self.cur_node = temp
            self.exp_type = "long"

            return lhs, rhs

        if "int" in (lhs.llvm_type, rhs.llvm_type):

            temp = self.cur_node

            self.cur_node = lhs
            lhs = self.select_type(
                IntType(32),
                "int",
                **type_casting["int"]
            )

            self.cur_node = rhs
            rhs = self.select_type(
                IntType(32),
                "int",
                **type_casting["int"]
            )

            self.cur_node = temp
            self.exp_type = "int"

            return lhs, rhs

        if "short" in (lhs.llvm_type, rhs.llvm_type):

            temp = self.cur_node

            self.cur_node = lhs
            lhs = self.select_type(
                IntType(16),
                "short",
                **type_casting["short"]
            )

            self.cur_node = rhs
            rhs = self.select_type(
                IntType(16),
                "short",
                **type_casting["short"]
            )

            self.cur_node = temp
            self.exp_type = "short"

            return lhs, rhs

        if "char" in (lhs.llvm_type, rhs.llvm_type):
            #this is different because of optimization
            if lhs == "bool":
                lhs.llvm_type = IntType(1)
                lhs = CastIntHigh(lhs, IntType(8), lhs.span)

            if rhs == "bool":
                rhs.llvm_type = IntType(1)
                rhs = CastIntHigh(rhs, IntType(8), rhs.span)

            self.exp_type = "char"

            return lhs, rhs

        # the default
        self.exp_type = "bool" # every operand is boolean
        return lhs, rhs

    def make_compatible(self, target: str, given: str) -> Node:

        # we assume that the rhs node is self.cur_node
        if target in ("", given, 0):

            self.exp_type = self.cur_node.llvm_type
            llvm_type = self.get_currect_type()

            self.cur_node.llvm_type = llvm_type

            return self.cur_node

        # else

        # bring the llvm type
        self.exp_type = target
        llvm_tp_target = self.get_currect_type()

        # select the type
        typed_res = self.select_type(
            llvm_tp_target,
            target,
            **type_casting[target]
        )

        # get currect type
        self.exp_type = typed_res.llvm_type
        llvm_type = self.get_currect_type()

        typed_res.llvm_type = llvm_type

        # return the type
        return typed_res

    def select_type(
        self,
        base_type, # llvm type instance
        base_str,
        **cast_types #the reference of casting type
    ) -> tuple[str, Node, None] | tuple[None, None, Exception]:

        current_type = ""

        if self.cur_node == "int":
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

        elif self.cur_node == "string":
            self.cur_node.llvm_type = IntType(8).as_pointer()
            current_type = "string"

        elif self.cur_node != base_str:
            self.diagctx.emit(Diagnostics(
                f"unable to cast {self.cur_node}",
                "S0297",
                self.cur_node.span
            ))

        if current_type in cast_types:

            if current_type == "string":
                self.diagctx.emit(Diagnostics(
                    "we can not convert string to something else",
                    "S0389",
                    self.cur_node.span
                ))
                return T_POISON

            #else
            return cast_types[current_type](self.cur_node, base_type)

        #else
        return self.cur_node

    #end
#end
