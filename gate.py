import numpy as np
import pandas as pd

def makeProd(n):
    if n <= 1:
        return [[0], [1]]
    return [j + [i] for j in makeProd(n-1) for i in range(2)]

def operate(prod, operator, out=False, reversed=False):

    a = []
    for p in prod:

        if out:
            print(f"operating {p}")

        if(reversed):
            p = p[::-1]

        red = p[0]
        for i in range(1, len(p)):
            result = 1 if operator[1](red, p[i]) else 0
            if out:
                print(f'{red} {operator[0]} {p[i]} == {result}')
            red = result

        a.append(red)
        if out:
            print(f"result = {red}\n")
    return a

AND = ['AND', lambda x, y: x and y]
NAND = ['NAND', lambda x, y: not (x and y)]

XOR = ['XOR', lambda x, y: x != y]
NXOR = ['NXOR', lambda x, y: x == y]



for n in [3,4]:

    prod = makeProd(n)
    d = pd.DataFrame(prod, columns=list('abcdefghijklmnopqrstuvwxyz')[:n])

    operator = [XOR, NXOR]
    for op in operator:
        result = operate(prod, op)
        d[op[0]] = result

    d['BOSU'] = d[operator[0][0]].values != d[operator[1][0]].values
    print(d)
    print()

"""
   a  b  c XOR NXOR   BOSU
0  0  0  0   0    0  False
1  0  0  1   1    1  False
2  0  1  0   1    1  False
3  0  1  1   0    0  False
4  1  0  0   1    1  False
5  1  0  1   0    0  False
6  1  1  0   0    0  False
7  1  1  1   1    1  False

    a  b  c  d XOR NXOR  BOSU
0   0  0  0  0   0    1  True
1   0  0  0  1   1    0  True
2   0  0  1  0   1    0  True
3   0  0  1  1   0    1  True
4   0  1  0  0   1    0  True
5   0  1  0  1   0    1  True
6   0  1  1  0   0    1  True
7   0  1  1  1   1    0  True
8   1  0  0  0   1    0  True
9   1  0  0  1   0    1  True
10  1  0  1  0   0    1  True
11  1  0  1  1   1    0  True
12  1  1  0  0   0    1  True
13  1  1  0  1   1    0  True
14  1  1  1  0   1    0  True
15  1  1  1  1   0    1  True
"""