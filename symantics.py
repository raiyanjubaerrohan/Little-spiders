from nodes import *
from llvmlite.ir import (
	FloatType,
	IntType,
	DoubleType,
	PointerType,
)

from utils import getCurrectType

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

    def __init__(self):
        self.cur_node = None
        self.exp_type = None

    def load(self, ast, ctx):
        self.cur_node = ast
        self.ctx = ctx

    def simanticize_varDecNode(self) -> tuple[Node | None, Exception | None]:
        varDec = self.cur_node
        self.cur_node = varDec.expr
        self.exp_type = varDec.value.llvm_type

        expr, err = self.simanticize()
        if err: return None, err

        self.cur_node = expr
        comp_res, err = self.make_compatible(
            varDec.value.llvm_type, expr.llvm_type
        )
        if err: return None, err
        
        #lastly assign the compatable result
        varDec.expr = comp_res
        varDec.value.llvm_type = comp_res.llvm_type

        return varDec, None

    def simanticize_varAssNode(self) -> tuple[Node | None, Exception | None]:

        node = self.cur_node

        self.exp_type = node.value.llvm_type
        self.cur_node = node.expr

        expr, err = self.simanticize()
        if err: return None, err

        self.cur_node = expr
        comp_res, err = self.make_compatible(
            node.value.llvm_type, expr.llvm_type
        )

        # I do not need the right type,
        # because I have one in
        # node.value.llvm_type

        return VarAssignNode(node.value, comp_res), None

    def simanticize_binOpNode(self):

        tree = self.cur_node

        ### lhs
        self.cur_node = tree.lhs
        res_lhs, err = self.simanticize()
        if err: return None, err
        if self.exp_type == "string":
            return None, Exception("@symanticizer, can not do operation with string")

        ### rhs
        self.cur_node = tree.rhs
        res_rhs, err = self.simanticize()
        if err: return None, err
        if self.exp_type == "string":
            return None, Exception("@symanticizer, can not do operation with string")

        ty_lhs, ty_rhs, err = self.align_type(
            res_lhs,
            res_rhs
        )
        if err: return None, err
        #this will set self.exp_type automatically

        binOp = BinOpNode(tree.value, ty_lhs, ty_rhs)
        binOp.llvm_type = self.exp_type

        return binOp, None


    def simanticize_compareNode(self):

        tree = self.cur_node

        ### lhs
        self.cur_node = tree.lhs
        res_lhs, err = self.simanticize()
        if err: return None, err
        if self.exp_type == "string":
            return None, Exception("can not compare string")

        ### rhs
        self.cur_node = tree.rhs
        res_rhs, err = self.simanticize()
        if err: return None, err
        if self.exp_type == "string":
            return None, Exception("can not compare string")

        ty_lhs, ty_rhs, err = self.align_type(
            res_lhs,
            res_rhs
        )
        if err: return None, err
        # this will set self.exp_type automatically

        cmpNode = CompareNode(tree.value, ty_lhs, ty_rhs)

        cmpNode.llvm_type = "bool"
        cmpNode.mean_type = self.exp_type

        self.exp_type = "bool"

        return cmpNode, None

    def simanticize(self) -> tuple[Node | None, Exception | None]:

        if isinstance(self.cur_node, VarDeclareNode):

            res, err = self.simanticize_varDecNode()
            if err: return None, err

            return res, None

        elif isinstance(self.cur_node, VarAssignNode):

            res, err = self.simanticize_varAssNode()
            if err: return None, err

            return res, None

        elif isinstance(self.cur_node, BinOpNode):

            res, err = self.simanticize_binOpNode()
            if err: return None, err

            return res, None

        elif isinstance(self.cur_node, CompareNode):

            res, err = self.simanticize_compareNode()
            if err: return None, err

            return res, None

        elif isinstance(self.cur_node, (ConstantNode, BitNode)):

            self.exp_type = self.cur_node.llvm_type

            return self.cur_node, None

        elif isinstance(self.cur_node, VarFetchNode):
        
            self.exp_type = self.cur_node.value.llvm_type
            self.cur_node.llvm_type = self.exp_type

            return self.cur_node, None

        elif isinstance(self.cur_node, NegNode):
            node = self.cur_node
            self.cur_node = node.value

            node, err = self.simanticize()
            if err: return None, err

            right_type, err = self.get_currect_type()
            if err: return None, err

            node.llvm_type = right_type

            return NegNode(node), None

        elif isinstance(self.cur_node, PosNode):
            node = self.cur_node
            self.cur_node = node.value

            node, err = self.simanticize()
            if err: return None, err

            right_type, err = self.get_currect_type()
            if err: return None, err

            node.llvm_type = right_type

            return PosNode(node), None

        elif isinstance(self.cur_node, StringNode):
            self.exp_type = "string"

            return self.cur_node, None

        elif isinstance(self.cur_node, CallNode):

            res, err = self.simanticize_callNode()
            if err: return None, err

            return res, None

        elif isinstance(self.cur_node, IfElseBlock):

            res, err = self.simanticize_ifElseBlock()
            if err : return None, err

            return res, None

        elif isinstance(self.cur_node, ElseBlock):

            res, err = self.simanticize_ElseBlock()
            if err: return None, err

            return res, None

        elif isinstance(self.cur_node, DefaultBlock):
            return self.cur_node, None
        #end
        return None, Exception(f"@symanticizer,the object ({self.cur_node}) did not match the list")

    def simanticize_callNode(self) -> tuple[CallNode | None, Exception | None]:
        node = self.cur_node

        # for the params
        if not node.llvm_type["var_args"]:
            g_params = len(node.params)
            e_params = len(node.llvm_type["params_type"])

            if g_params != e_params:
                return None, Exception(
                    f"@symanticizer, the function takes {e_params} args "
                    f"but you have passed {g_params} args"
                )
            #else

            typed_params = []

            for n in range(g_params): # or e_params
                self.exp_type = node.llvm_type["params_type"][n]
                self.cur_node = node.params[n]

                res, err = self.simanticize()
                if err: return None, err

                self.cur_node = res
                comp_res, err = self.make_compatible(
                    node.llvm_type["params_type"][n],
                    res.llvm_type
                )
                if err : return None, err

                typed_params.append(comp_res)

            callNode = CallNode(node.value, typed_params)
            callNode.llvm_type = node.llvm_type["ret_type"]

            self.exp_type = callNode.llvm_type

            return callNode, None

        #else
        g_params = len(node.params)
        e_params = len(node.llvm_type["params_type"])

        if g_params < e_params: # the opposite case
            return None, Exception(
                f"@symanticizer, the function takes {e_params} "
                f"but you have passed {g_params} args"
            )

        typed_params = []
        n = 0

        while n < e_params:
            self.cur_node = node.params[n]
            self.exp_type = node.llvm_type["params_type"][n]

            # simanticize
            res, err = self.simanticize()
            if err: return None, err

            # make compatible
            self.cur_node = res
            comp_res, err = self.make_compatible(
                node.llvm_type["params_type"][n],
                res.llvm_type
            )
            if err: return None, err

            typed_params.append(comp_res)

            n += 1

        while n < g_params:
            self.cur_node = node.params[n]
            self.exp_type = ""

            # simanticize
            res, err = self.simanticize()
            if err: return None, err

            # get llvm type
            self.exp_type = res.llvm_type
            llvm_type, err = self.get_currect_type()
            if err: return None, err

            typed_params.append(res)

            n += 1

        callNode = CallNode(node.value, typed_params)
        callNode.llvm_type = node.llvm_type["ret_type"]

        self.exp_type = callNode.llvm_type

        return callNode, None

    def simanticize_ifElseBlock(self) -> tuple[IfElseBlock | None, Exception | None]:

        if_block = self.cur_node

        # the condition
        self.cur_node = if_block.cond
        res_cond, err = self.simanticize()
        if err: return None, err

        res_cond.llvm_type = IntType(1) #currecting the type

        # the body
        stmts = []

        for stm in if_block.body:
            self.cur_node = stm

            res, err = self.simanticize()
            if err: return None, err

            stmts.append(res)

        # the else block
        self.cur_node = if_block.else_block
        res_else_block, err = self.simanticize()
        if err: return None, err

        return IfElseBlock(res_cond, stmts, res_else_block), None

    def simanticize_ElseBlock(self):

        else_block = self.cur_node

        stmts = []

        for stm in else_block.body:
            self.cur_node = stm

            res, err = self.simanticize()
            if err: return None, err

            stmts.append(res)

        return ElseBlock(stmts), None

    def get_currect_type(self) -> tuple[
        IntType | DoubleType | FloatType | PointerType | None,
        Exception | None
    ]:
        if self.exp_type == "int":
            return IntType(32), None

        elif self.exp_type == "short":
            return IntType(16), None

        elif self.exp_type == "char":
            return IntType(8), None

        elif self.exp_type == "bool":
            return IntType(1), None

        elif self.exp_type == "double":
            return DoubleType(), None

        elif self.exp_type == "float":
            return FloatType(), None

        elif self.exp_type == "string":
            return IntType(8).as_pointer(), None

        else:
            return None, Exception(f"@symanticizer, no type matched")

    def align_type(self, lhs, rhs) -> tuple[
        Node, Node, None] | tuple[None, None, Exception
        ]:

        if "double" in (lhs.llvm_type, rhs.llvm_type):
            #equals to
            #lhs or rhs is "double"

            temp = self.cur_node
            #temporary var to store the current node

            self.cur_node = lhs #for passing in select_type

            _, lhs, err = self.select_type(
                DoubleType(),
                "double",
                **type_casting["double"]
            )
            if err: return None, None, err

            self.cur_node = rhs
            _, rhs, err = self.select_type(
                DoubleType(),
                "double",
                **type_casting["double"]
            )
            if err: return None, None, err

            #at very end reassign the current node to be currect
            self.cur_node = temp
            self.exp_type = "double"

            return lhs, rhs, None

        if "float" in (lhs.llvm_type, rhs.llvm_type):

            #same as upper check
            temp = self.cur_node

            self.cur_node = lhs
            _, lhs, err = self.select_type(
                FloatType(),
                "float",
                **type_casting["float"]
            )
            if err: return None, None, err

            self.cur_node = rhs
            _, rhs, err = self.select_type(
                FloatType(),
                "float",
                **type_casting["float"]
            )
            if err: return None, None, err

            self.cur_node = temp
            self.exp_type = "float"

            return lhs, rhs, None

        if "long" in (lhs.llvm_type, rhs.llvm_type):
            temp = self.cur_node

            self.cur_node = lhs
            _, lhs, err = self.select_type(
                IntType(64),
                "long",
                **type_casting["long"]
            )
            if err: return None, None, err

            self.cur_node = rhs
            _, rhs, err = self.select_type(
                IntType(64),
                "long",
                **type_casting["long"]
            )
            if err: return None, None, err

            self.cur_node = temp
            self.exp_type = "long"

            return lhs, rhs, None

        if "int" in (lhs.llvm_type, rhs.llvm_type):

            temp = self.cur_node

            self.cur_node = lhs
            _, lhs, err = self.select_type(
                IntType(32),
                "int",
                **type_casting["int"]
            )
            if err: return None, None, err

            self.cur_node = rhs
            _, rhs, err  = self.select_type(
                IntType(32),
                "int",
                **type_casting["int"]
            )
            if err: return None, None, err

            self.cur_node = temp
            self.exp_type = "int"

            return lhs, rhs, None

        if "short" in (lhs.llvm_type, rhs.llvm_type):

            temp = self.cur_node

            self.cur_node = lhs
            _, lhs, err  = self.select_type(
                IntType(16),
                "short",
                **type_casting["short"]
            )
            if err: return None, None, err

            self.cur_node = rhs
            _, rhs, err = self.select_type(
                IntType(16),
                "short",
                **type_casting["short"]
            )
            if err: return None, None, err

            self.cur_node = temp
            self.exp_type = "short"

            return lhs, rhs, None

        if "char" in (lhs.llvm_type, rhs.llvm_type):
            #this is different because of optimization
            if lhs == "bool":
                lhs.llvm_type = IntType(1)
                lhs = CastIntHigh(lhs, IntType(8))

            if rhs == "bool":
                rhs.llvm_type = IntType(1)
                rhs = CastIntHigh(rhs, IntType(8))

            self.exp_type = "char"

            return lhs, rhs, None

        self.exp_type = "bool" # every operand is boolean
        return lhs, rhs

        #end
    #end

    def make_compatible(self, target: str, given: str) -> tuple[
        Node | None, Exception | None
    ]:
        # we assume that the rhs node is self.cur_node
        if target in ("", given, 0):

            self.exp_type = self.cur_node.llvm_type
            llvm_type, err = self.get_currect_type()
            if err: return None, err

            self.cur_node.llvm_type = llvm_type

            return self.cur_node, None

        # else

        # bring the llvm type
        self.exp_type = target
        llvm_tp_target, err = self.get_currect_type()
        if err: return None, err

        # select the type
        _, typed_res, err = self.select_type(
            llvm_tp_target,
            target,
            **type_casting[target]
        )
        if err: return None, err

        # get currect type
        self.exp_type = typed_res.llvm_type
        llvm_type, err = self.get_currect_type()
        if err: return None, err

        typed_res.llvm_type = llvm_type

        # return the type
        return typed_res, None

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
            return None, None, Exception(f"@symanticizer, unable to cast {self.cur_node}")

        if current_type in cast_types:

            if current_type == "string":
                return None, None, Exception(
                    "@symanticizer, sorry but we can "
                    "not convert string to something else"
                )

            #else
            return base_str, cast_types[current_type](
                self.cur_node,
                base_type
            ), None

        #else
        return base_str, self.cur_node, None

    #end
#end
