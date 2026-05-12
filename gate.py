import pandas as pd

class Operator:
    def __init__(self, name, func):
        self.name = name
        self.func = func

AND = Operator('AND', lambda x, y: x and y)
NAND = Operator('NAND', lambda x, y: not (x and y))

OR = Operator('OR', lambda x, y: x or y)
NOR = Operator('NOR', lambda x, y: not (x or y))

XOR = Operator('XOR', lambda x, y: x != y)
NXOR = Operator('NXOR', lambda x, y: x == y)

class Setting:
    def __init__(self, *operators, reversed=False):
        self.operators = operators
        self.reversed = reversed

class Gate:

    @staticmethod
    def makeProd(n):
        yield from (tuple(map(int, format(i, f'0{n}b'))) for i in range(2**n))

    @staticmethod
    def operateVariable(variable, setting, out):

        length = len(variable)

        if length - 1 != len(setting.operators):
            raise ValueError(f'{length -1}개의 연산자가 필요합니다.')
        
        varn = 'abcdefghijklmnopqrstuvwxyz'

        out.setdefault('variable', []).append(variable)

        if setting.reversed:

            cal = variable[-1]

            out.setdefault(varn[length -1], []).append(variable[length -1])

            for i in range(length - 2, -1, -1):
                cal = 1 if setting.operators[i].func(variable[i], cal) else 0

                out.setdefault(f'{setting.operators[i].name} {varn[i]}', []).append(variable[i])
                out.setdefault(f'R{length - i -2}', []).append(cal)

            return cal
        

        cal = variable[0]

        out.setdefault(varn[0], []).append(variable[0])

        for i in range(0, length - 1):

            cal = 1 if setting.operators[i].func(cal, variable[i + 1]) else 0

            out.setdefault(f'{setting.operators[i].name} {varn[i + 1]}', []).append(variable[i + 1])
            out.setdefault(f'R{i}', []).append(cal)

        return cal

    @staticmethod
    def title(setting):
        varn = 'abcdefghijklmnopqrstuvwxyz'

        if setting.reversed:
            return f"{' '.join([f'({varn[i]} {g.name}' for i, g in enumerate(setting.operators)])} {varn[len(setting.operators)]}{')' * len(setting.operators)}"

        return f"{'(' * len(setting.operators)}{varn[0]} {' '.join([f'{g.name} {varn[i+1]})' for i, g in enumerate(setting.operators)])}"


    @staticmethod
    def do(setting):

        out = {}
        for p in Gate.makeProd(len(setting.operators) + 1):
            Gate.operateVariable(p, setting, out)

        return pd.DataFrame(out).set_index('variable')


    @staticmethod
    def compare(*settings, checkSame=False):
        df = pd.DataFrame([Gate.do(setting).iloc[:, -1] for setting in settings], index=[Gate.title(setting) for setting in settings])
        if checkSame:
            df.loc['isSame'] = (df.nunique() == 1).astype(int)
        return df

set0 = Setting(XOR, AND, reversed=False)
print("cal::", Gate.title(set0))
print(Gate.do(set0))

print()

set1 = Setting(XOR, AND, reversed=True)
print("cal::", Gate.title(set1))
print(Gate.do(set1))

print(Gate.compare(Setting(NAND, NAND, reversed=True), Setting(NAND, NAND)))

print(Gate.compare(Setting(XOR, XOR), Setting(NXOR, NXOR)))

print(Gate.compare(Setting(XOR, XOR), Setting(NXOR, XOR), checkSame=True))