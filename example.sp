let x = -1;

while x < 10 {
	x = x + 1;
	if x == 5 or x == 7 {break;}
	print("x is %d\n", x);
} else {
	print("the loop breaked because\nthe condition became false\n");
}

print("successfully completed!\n");
