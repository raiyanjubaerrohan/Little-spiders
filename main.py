from lexical import *
from parserize import *
from symanticizer import *
from utils import T_EOF
import argparse

from llvmlite import ir


#parsing the arguments
argParser = argparse.ArgumentParser(prog="spiders")
argParser.add_argument(
    "file",
    nargs="?",
    help="Source file"
)
argParser.add_argument(
    "--display-llvm",
    action="store_true",
    help="displays the llvm ir on the console"
)
args = argParser.parse_args()
#complete set


lexer = Lexer()
parser = Parser()
simantics = Symantics()

module = ir.Module(name= args.file if args.file else "stdmodule")
module.triple = "aarch64-unknown-linux-android24"
module.data_layout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i8:8:32-i16:16:32-i64:64-i128:128-n32:64-S128-Fn32"

mainfunc = ir.Function(
    module,
    ir.FunctionType(
        ir.IntType(32),
        ()
    ),
    "main"
)

builder = ir.IRBuilder(
    mainfunc.append_basic_block(name="entry")
)

if not args.file:
    print("error: no file input")
    exit(0)

err_msg = "compile time error : {0}"

f = open(args.file, "r")

theEnd = False

while not theEnd:
    line = f.readline()

    if line == "":
        tokens = [Token(T_EOF)]
        err = None
    else:
        tokens, err = lexer.lex(line)

    if err: 
        print(err_msg.format(err))
        exit(0)

    parser.consume(tokens)

    while True:
        tlast, err = parser.parse()
        #tlast is Type Less Abstract Syntax Tree

        if tlast == "needed":
            break

        elif tlast == "theend":
            theEnd = True
            break
                
        elif err:
            print(err_msg.format(err))
            exit(0)

        simantics.load(tlast)
        _, tpast = simantics.simanticize()

        if tpast is not None:
            tpast.codegen(builder)


f.close()

#manual thing for testing
#will be automated soon...
builder.ret(ir.Constant(ir.IntType(32),0))

if args.display_llvm:
    print(module)

outputFile = open("tester.ll", "w")
outputFile.write(str(module))

