import argparse, sys, os

from lexical import Lexer
from parserize import Parser
from symantics import Symanticizer
from utils import Context, CodegenError
from resolvistics import Resolver
from diagnostical import DiagContext
from llvmlite import ir

#parsing the arguments
argParser = argparse.ArgumentParser(prog="spiders")

argParser.add_argument("input_file", nargs="?",
    help="the source file name")
argParser.add_argument("-o", "--output", nargs=1, default=["tester.ll"],
    help="output file name (default tester.ll)")
argParser.add_argument("-p", "--print-llvm",
    action="store_true", help="prints the LLVM IR")
argParser.add_argument("-d", "--debug", action="store_true",
    help="enables debug mode")
argParser.add_argument("-t", "--target", nargs=1, default=["aarch64-unknown-linux-android24"],
    help="optional custom target triple")

args = argParser.parse_args()

if args.input_file and os.path.exists(args.input_file):
    f = open(args.input_file, mode="rt", encoding="utf-8")
    content = f.read()
    f.close()
else:
    print("error: you haven't passed any input file or the file does not exists")
    sys.exit(1)

# the module
module = ir.Module(name=args.input_file)
module.triple = args.target[0]
module.data_layout = ("e-m:e-p270:32:32-p271:32:32-p272:64:64-"+
"i8:8:32-i16:16:32-i64:64-i128:128-n32:64-S128-Fn32")

#main function (temporary)
mainfunc = ir.Function(
    module,
    ir.FunctionType(ir.IntType(32), ()),
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

# context
ctx = Context(
    ir.IRBuilder(mainfunc.append_basic_block(name="entry")),
    module
)
diagctx = DiagContext(content)

ctx.add_func_entry(
    name="print",
    ptr=printFunc,
    ret_type="int",
    params_type=["string"],
    var_arg=True
)

# init custom modules
lexer = Lexer(content, diagctx)
parser = Parser(diagctx)
simanticizer = Symanticizer(diagctx)
resolver = Resolver(diagctx)

# debug just the moment before
if args.debug: breakpoint()

# running lexer becuse lexer can tokenize an entire file
tokens = lexer.lex()
if diagctx.has_error():
    diagctx.render()
    sys.exit(1)

if eof := parser.load(tokens):
    print("the given file is empty")
    sys.exit(0)

# the loop (temporary)
running = True
while running:
    # parse
    raw_ast = parser.parse()
    if raw_ast == "theend": running = False

    # resolve
    resolver.load(raw_ast, ctx)
    sym_ast = resolver.resolve()

    print(sym_ast, '\n')

    # simanticize
    #simanticizer.load(sym_ast)
    #complete_ast = simanticizer.simanticize()

    #if diagctx.has_error(): break

    #try: ctx = complete_ast.codegen(ctx)
    #except CodegenError as ce:
        #print(f"codegen error: {ce}")

if diagctx.has_error():
    diagctx.render()
    sys.exit(1)

#manual thing for testing
#will be automated soon...
ctx.builder.ret(ir.Constant(ir.IntType(32),0))

if args.print_llvm:
    print(module)

with open(args.output[0], mode="w", encoding="utf-8") as outputFile:
    outputFile.write(str(module))
    outputFile.close()
