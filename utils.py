from llvmlite.ir import IntType, HalfType, FloatType, DoubleType
from llvmlite.ir import IRBuilder

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
    "else",
    "elif",
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

    if isinstance(ty, IntType):

        if ty.width == 64: return "long"
        if ty.width == 32: return "int"
        if ty.width == 16: return "short"
        if ty.width == 8 : return "char"
        if ty.width == 1 : return "bool"

    elif isinstance(ty, HalfType):
        return "half"

    elif isinstance(ty, FloatType):
        return "float"

    elif isinstance(ty, DoubleType):
        return "double"

    #else
    return ""

def cutOut(l:list, start:int, end:int | bool = False):

    if not end and isinstance(end, bool): end = len(l) - 1 # the last index

    out = []
    
    for i in range(len(l)):

        # if not in range
        if not (i >= start and i <= end):
            out.append(l[i])

    return out

class Position:
	def __init__(self, start_pos: int = 0, end_pos: int = 1):
		self.start_pos = start_pos
		self.end_pos = end_pos
		
	def set_start(self, st) -> None:
		self.start_pos = st
		
	def set_end(self, ed) -> None:
		self.end_pos = ed

class Context:
    def __init__(self):
        self.builder = None
        self.merge_block = None
        self.variables_ptr = {}
        # will be added later on
