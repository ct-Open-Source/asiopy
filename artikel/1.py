#!/usr/bin/env python3

import time

def a():
    print("a()")
    time.sleep(2)
    print(f"a() {time.time()-t0:.1f}s")
    
def b():
    print("b()")
    time.sleep(1)
    print(f"b() {time.time()-t0:.1f}s")

t0 = time.time()
def main():
    a()
    b()

main()