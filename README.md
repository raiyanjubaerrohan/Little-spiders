# Little-spiders
This project is a compiler front end project with llvmlite.
This is a part time project for learning systems. 
This is basically C but with more dynamic and easy syntax. 
This depends on clang to compile.
This is just for fun. I find fun making systems.

# Installing dependencies

It depends on python package llvmlite. Llvmlite in a suitable pacakge to write this .
Install llvmlite with this command on **Anaconda environment**:
```bash
conda install llvmlite
```
Or install it with **pip**:
```bash
pip install llvmlite
```

if it doesn't install and show errors, then just manually install llvmlite.
This is the only way left. besides you read bellow.

It also depents on clang to compile the raw llvm IR.
I have said, "It is just C but more powerful."
This is build on top of C's ABI. 
So we gonna need clang.

## For *windows* users,
first create a virtual environment.
```bash
python -m venv .venv
.venv/Scripts/activate
```

then install it.
```bash
pip install llvmlite
```

## For linux users

if you are using ubuntu, you have a clean path
```bash
sudo apt update
sudo apt python3-dev python3-pip build-essential llvm-dev
```

then create a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate
```

then install llvmlite
```bash
pip install llvmlite
```

And if you are using Arch BTW
Install dependecies:

```bash
sudo pacman -S python python-pip base-devel llvm
```

create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```
after that just run

```bash
pip install llvmlite
```

# For macOS users

I do not how to install it on macOS. so good luck.

## If it crashes
I have a limited expirence with llvmlite.
I can not tell how to install it properly.
You have to find the way by yourself. I can not help you. Sorry.


## Else
That all we need to get our system set.

