from llvmlite.ir import (
    IntType,
    FloatType,
    DoubleType,
    PointerType,
)

T_ADD       = "ADD"
T_SUB       = "SUB"
T_MUL       = "MUL"
T_DIV       = "DIV"
T_MOD       = "MOD"
T_EQ        = "EQ"
T_EQS       = "EQS"
T_NEQ       = "NEQ"
T_LT        = "LT"
T_LTE       = "LTE"
T_GT        = "GT"
T_GTE       = "GTE"
T_ARROW     = "ARROW"
T_IDEN      = "IDEN"
T_LITERAL   = "LITERAL"
T_KEY       = "KEY"
T_QUS       = "QUS"
T_EOS       = "EOS"
T_EOF       = "EOF"
T_COLON     = "COLON"
T_COMMA     = "COMMA"
T_SQUTE     = "SQUTE"

T_LPAN1     = "LPAN1"
T_RPAN1     = "RPAN1"
T_LPAN2     = "LPAN2"
T_RPAN2     = "RPAN2"
T_LPAN3     = "LPAN3"
T_RPAN3     = "RPAN3"


NUMBERS     = "0123456789"
ALPHABETS_U = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ALPHABETS_L = "abcdefghijklmnopqrstuvwxyz"
ALPHABETS   = ALPHABETS_L + ALPHABETS_U


keywords = [
    "if",
    "elif",
    "else",
    "while",
    "let",
    "int",
    "float",
    "char",
    "short",
    "double",
    "bool",
    "func",
    "end",
]


def getCurrectType(ty) -> str:

    str_repr = ""

    if isinstance(ty, IntType):

        if ty.width == 64: str_repr = "long"
        if ty.width == 32: str_repr = "int"
        if ty.width == 16: str_repr = "short"
        if ty.width == 8 : str_repr = "char"
        if ty.width == 1 : str_repr = "bool"

    elif isinstance(ty, FloatType):
        str_repr = "float"

    elif isinstance(ty, DoubleType):
        str_repr = "double"

    elif isinstance(ty, PointerType):

        res = getCurrectType(ty.pointee)

        if res == "": pass
        elif res == "char": str_repr = "string"
        else: str_repr = res + "ptr"

    return str_repr

def get_generator():
    n = 0
    while True:
        yield "stringno"+str(n)
        n += 1

names = get_generator()

def name_generator():
    return next(names)

class Position:
    def __init__(self, start_pos: int = 0, end_pos: int = 1):
        self.start_pos = start_pos
        self.end_pos = end_pos

    def __repr__(self):
        return f"Position({self.start_pos}->{self.end_pos})"

class Context:
    def __init__(self):
        self.builder = None
        self.merge_block = None
        self.function_ptr = {}
        # we have to put one element at least
        self.module = None
        self.suc_value = None
        # will be added later on

    def initial(self, builder, module):
        self.builder = builder
        self.module = module

    def add_func_entry(self, name, ptr, ret_type, params_type, var_arg):
        self.function_ptr[name] = {
            "value": ptr,
            "type": {
                "ret_type": ret_type,
                "params_type": params_type,
                "var_arg": var_arg
            }
        }

    def __repr__(self):
        return "this is a context, so no repr is impled."

class Symbol:
    def __init__(self):
        self.name = None
        self.llvm_type = None
        self.ptr = None

    def __repr__(self):
        return f"Sym({self.name}=>{self.llvm_type} at {self.ptr})"
