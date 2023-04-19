#!/usr/bin/env python3

import asyncio
import time

async def a():
    print("a()")
    await asyncio.sleep(2)
    print(f"a() {time.time()-t0:.1f}s")
    
async def b():
    print("b()")
    await asyncio.sleep(1)
    print(f"b() {time.time()-t0:.1f}s")

t0 = time.time()
async def main():
    task1 = asyncio.create_task(a())
    task2 = asyncio.create_task(b())
    await task1
    await task2

asyncio.run(main())
