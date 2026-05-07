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
This is the only way left.

It also depents on clang to compile the raw llvm IR.
I have said, "It is just C but more powerful."
This is build on top of C's ABI. 
So we gonna need clang.

For *windows* users, I recommand that you goto google and make a quick search about it.
And for *linux* users, you should have it pre-installed but if not
you can run this:
	for ubuntu:
	```bash
	sudo apt install clang
	```

	for arch:
	```bash
	pacman -S clang
	```

That all we need to get our system set.

