import numpy as np
import pandas as pd

class Operator:
    def __init__(self, name, op, reversed=False):
        self.name = name
        self.op = op
        self.reversed = reversed

def makeProd(n):
    if n <= 1:
        return [[0], [1]]
    return [j + [i] for j in makeProd(n-1) for i in range(2)]

def operate(prod, operator, out=False,):

    a = []
    for p in prod:

        if out:
            print(f"operating {p}")

        if operator.reversed:
            p = p[::-1]

        red = p[0]

        for i in range(1, len(p)):
            if operator.reversed:
                result = 1 if operator.op(p[i], red) else 0
            else:
                result = 1 if operator.op(red, p[i]) else 0
            if out:
                print(f'{red} {operator.name} {p[i]} == {result}')
            red = result

        a.append(red)
        if out:
            print(f"result = {red}\n")
    return a

def do(n, operator0, operator1):
    prod = makeProd(n)
    d = pd.DataFrame(prod, columns=list('abcdefghijklmnopqrstuvwxyz')[:n])

    d[operator0.name] = operate(prod, operator0)
    d[operator1.name] = operate(prod, operator1)

    d[f'BOSU {operator0.name}-{operator1.name}'] = d[operator0.name].values != d[operator1.name].values
    print(d)
    print()



AND = Operator('AND', lambda x, y: x and y)
NAND = Operator('NAND', lambda x, y: not (x and y))
RNAND = Operator('RNAND', lambda x, y: not (x and y), True)

XOR = Operator('XOR', lambda x, y: x != y)
NXOR = Operator('NXOR', lambda x, y: x == y)

for n in [3,4]:
    do(n, XOR, NXOR)

for n in [3,4]:
    do(n, NAND, RNAND)
