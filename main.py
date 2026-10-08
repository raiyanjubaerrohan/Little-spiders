from parserize import Parser
from symantics import Symanticizer
from utils import Context
from resolvistics import Resolver
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

# printf function (build-in)
printFunc = ir.Function(
    module,
    ir.FunctionType(
        ir.IntType(32),
        (ir.IntType(8).as_pointer(), ),
        var_arg=True
    ),
    "printf"
)

#context
ctx = Context()

ctx.builder = ir.IRBuilder(
    mainfunc.append_basic_block(name="entry")
)
ctx.module = module

# the function entry
ctx.function_ptr["print"] = {
    "value": printFunc,
    "type": {
        "ret_type": "int",
        "params_type": ["string"],
        "var_args": True
    }
}

# init custom modules
parser = Parser()
simanticizer = Symanticizer()
resolver = Resolver()

if not args.file:
    print("error: no file input")
    exit(0)

err_msg = "compile time error : {0}"
f = open(args.file, "r")
theEnd = False

# set the context for modules
parser.set_context(ctx, f)
pexit, err = parser.start_up()
if pexit:
    print("there is nothing to parse!!")
    exit(0)

if err:
    print(err_msg.format(err))
    exit(1)

while not theEnd:

    # the parsing area
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

    print(tlast, '\n')

    # the resolver area
    resolver.load(tlast, ctx)
    if err := resolver.resolve():
        print(err_msg.format(err))
        exit(1)

    # the simantics area
    simanticizer.load(tlast, ctx)
    tpast, err = simanticizer.simanticize()
    if err:
        print(err_msg.format(err))
        exit(1)

    # the codegen line
    ctx = tpast.codegen(ctx)

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

