from parserize import Parser
from symanticizer import Symantics
from utils import Context
import argparse

from llvmlite import ir


#parsing the arguments
argParser = argparse.ArgumentParser(prog="spiders")

argParser.add_argument(
    "file",
    nargs="?",
    help="Source file name"
)

argParser.add_argument(
    "output",
    nargs="?",
    help="output file name"
)

argParser.add_argument(
    "--display-llvm",
    action="store_true",
    help="displays the llvm ir on the console"
)

args = argParser.parse_args()

#complete set
parser = Parser()
simantics = Symantics()

#the module
module = ir.Module(name= args.file if args.file else "stdmodule")
module.triple = "aarch64-unknown-linux-android24"
module.data_layout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i8:8:32-i16:16:32-i64:64-i128:128-n32:64-S128-Fn32"

#main function (temporary)
mainfunc = ir.Function(
    module,
    ir.FunctionType(
        ir.IntType(32),
        ()
    ),
    "main"
)

#context
ctx = Context()

ctx.builder = ir.IRBuilder(
    mainfunc.append_basic_block(name="entry")
)
ctx.module = module

if not args.file:
    print("error: no file input")
    exit(0)

err_msg = "compile time error : {0}"
f = open(args.file, "r")
theEnd = False

# set the context for the parser
parser.set_context(ctx, f)

while not theEnd:

    tlast, err = parser.parse()

    if tlast == "theend":
        theEnd = True
        if err:
            print(err_msg.format(err))
            exit(1)
        break
                
    elif err:
        print(err_msg.format(err))
        exit(1)

    simantics.load(tlast)
    res, err = simantics.simanticize()
    if err:
        print(err_msg.format(err))
        exit(1)

    ctx = res.codegen(ctx)


f.close()

#manual thing for testing
#will be automated soon...
ctx.builder.ret(ir.Constant(ir.IntType(32),0))

if args.display_llvm:
    print(module)

if args.output:
    outputFile = open(args.output, "w")
else:
    outputFile = open("tester.ll", "w")

outputFile.write(str(module))
outputFile.close()

