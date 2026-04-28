from lexical import *
from parserize import *
from llvmlite import ir
from symanticizer import *
from utils import variables_ptr

module = ir.Module(name="main")
module.triple = "aarch64-unknown-linux-android24"
module.data_layout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i8:8:32-i16:16:32-i64:64-i128:128-n32:64-S128-Fn32"

i32 = ir.IntType(32)

#adding printf definition
printffn = ir.Function(
    module,
    ir.FunctionType(
        ir.IntType(32),
        [ir.PointerType(ir.IntType(8))],
        var_arg = True
    ),
    "printf"
)

#adding a string to show answer
thestr = "ans: %f \n\0"
arr = ir.ArrayType(
    ir.IntType(8),
    len(thestr)
)

cstr = ir.Constant(arr, bytearray(thestr, "utf-8"))

gv = ir.GlobalVariable(module, arr, "string1")

gv.unnamed_addr = True
gv.global_constant = True
gv.linkage = "private"
gv.align = 1
gv.initializer = cstr

#building main

fnty = ir.FunctionType(i32, ())
mainfunc = ir.Function(module, fnty, "main")
builder = ir.IRBuilder(
    mainfunc.append_basic_block(name="entry")
)




def build(text:str):

    global builder
    
    lexer = Lexer(text)
    result, err = lexer.lex()
    if err: return None, err

    parser = Parser(result)
    typeless_node, err = parser.parse()

    if err: return None, err

    symanter = Symantics(typeless_node)
    exp_type, typed_node = symanter.simanticize(typeless_node)

    print(typed_node)
    
    ans_false = typed_node.codegen(builder)

    if not ans_false:
        return None, "there is a problem while parsing"

    return typed_node, None


#printf call builder and return
def commiter(ans):

    ptr = builder.gep(gv, [i32(0), i32(0)])
    builder.call(printffn, (ptr,ans))
    builder.ret(i32(0))

    print(module)

    with open("tester.ll","w") as f:
        f.write(str(module))

    
    

