class Operator:
    def __init__(self, name, handler, createLabel):
        self.name = name
        self.handler = handler
        self.createLabel = createLabel

    def __call__(self, *args):
        return self.handler(*args)

AND = Operator('AND', lambda *x: int(all(x)), lambda *x: f"({''.join(x)})")
NAND = Operator('NAND', lambda *x: int(not all(x)), lambda *x: f"({''.join(x)})'")

OR = Operator('OR', lambda *x: int(any(x)), lambda *x: f"({'+'.join(x)})'")
NOR = Operator('NOR', lambda *x: int(not any(x)), lambda *x: f"({'+'.join(x)})'")

XOR = Operator('XOR', lambda *x: int(sum((bool(xi) for xi in x)) % 2), lambda *x: f"({'⊕ '.join(x)})'")
NXOR = Operator('NXOR', lambda x, y: int(bool(x) == bool(y)), lambda x, y: f"({x}⊙ {y})")

NOT = Operator("NOT", lambda x: int(not x), lambda x: f"{x}'")

class Component:
    def __init__(self, label):
        self._label = label

    @property
    def label(self):
        return self._label

    def __invert__(self):
        return Expression(NOT, self)

    def __mul__(self, other):
        if isinstance(other, int):
            other = Constant(f"{other}", int(other))
        return Expression(AND, self, other)
    
    def __rmul__(self, other):
        if isinstance(other, int):
            other = Constant(f"{other}", int(other))
        return Expression(AND, other, self)
    
    def __and__(self, other):
        return self.__mul__(other)
    
    def __rand__(self, other):
        return self.__rmul__(other)
    
    def __add__(self, other):
        if isinstance(other, int):
            other = Constant(f"{other}", int(other))
        return Expression(OR, self, other)
    
    def __radd__(self, other):
        if isinstance(other, int):
            other = Constant(f"{other}", int(other))
        return Expression(OR, other, self)

    def __or__(self, other):
        return self.__add__(other)

    def __ror__(self, other):
        return self.__radd__(other)
    
    def __xor__(self, other):
        if isinstance(other, int):
            other = Constant(f"{other}", int(other))
        return Expression(XOR, self, other)

    def __rxor__(self, other):
        if isinstance(other, int):
            other = Constant(f"{other}", int(other))
        return Expression(XOR, other, self)

    def nand(self, other):
        if isinstance(other, int):
            other = Constant(f"{other}", int(other))
        return Expression(NAND, self, other)
    
    def nor(self, other):
        if isinstance(other, int):
            other = Constant(f"{other}", int(other))
        return Expression(NOR, self, other)
    
    def nxor(self, other):
        if isinstance(other, int):
            other = Constant(f"{other}", int(other))
        return Expression(NXOR, self, other)
    
    @staticmethod
    def and_n(*components):
        return Expression(AND, *components)

    @staticmethod
    def nand_n(*components):
        return Expression(NAND, *components)
    
    @staticmethod
    def or_n(*components):
        return Expression(OR, *components)

    @staticmethod
    def nor_n(*components):
        return Expression(NOR, *components)
    
    @staticmethod
    def xor_n(*components):
        return Expression(XOR, *components)

    def __str__(self):
        return self.label
    
class VariableComponent(Component):
    pass

class ConstComponent(Component):
    def __init__(self, label, value):
        super().__init__(label)
        self._value = int(value)
    
    @property
    def value(self):
        return self._value

    def __str__(self):
        return f"{self.label} = {self.value}"

class Variable(VariableComponent):
    def __repr__(self):
        return f"Variable(label={self.label})"

class Constant(ConstComponent):
    def __repr__(self):
        return f"Constant(label={self.label}, value={self.value})"

class EvaluatedResult(ConstComponent):
    def __repr__(self):
        return f"Evaluated(label={self.label}, value={self.value})"

class Expression(Component):
    def __init__(self, operator, *terms):
        super().__init__(None)

        self.terms = terms
        self.operator = operator

        self.usedVariables = self._combineUsedVariables(terms)

    def __str__(self):
        return f"F({', '.join(v.label for v in self.usedVariables)}) = {self.label}"

    def __repr__(self):
        return f"Expression(label={self.label})"

    @property
    def label(self):
        return self.operator.createLabel(*(term.label for term in self.terms))
    
    @property
    def usedVariables(self):
        return self._usedVariables
    
    @usedVariables.setter
    def usedVariables(self, usedVariables):
        self._usedVariables = tuple(dict.fromkeys(usedVariables))

    # requiedVariables: a, b, c
    # F(1, 0, 1)
    # F(1, 0, 1, 1): 4번째 1은 필요없으므로 무시됨.
    # F(a=1, b=0, c=1)
    # F(a=1, b=0, c=1, d=1): d 는 필요한 변수 목록에 없으므로 무시됨.
    # F(1, 0, 1, keepLabels=True)
    # F(a=1, b=0, c=1, keepLabels=True)
    def __call__(self, *args, keepLabels=False, **kargs):

        if args and kargs:
            raise TypeError("위치 인자와 키워드 인자를 동시 사용할 수 없습니다. F(0, 0) 또는 F(a=0, b=0) 형태로 통일이 필요합니다.")

        if args:
            valuesDict = dict(zip((v.label for v in self.usedVariables), args))
        elif kargs:
            valuesDict = kargs

        terms = [self._resolve(term, valuesDict, keepLabels) for term in self.terms]

        if any(v.label not in valuesDict for v in self.usedVariables):
            return Expression(self.operator, *terms)
        
        return EvaluatedResult(
            self.operator.createLabel(*(term.label for term in terms)),
            self.operator(*(term.value for term in terms))
        )
    
    @staticmethod
    def _resolve(component, values, keepLabels):
        if isinstance(component, Expression):
            return component(**values, keepLabels=keepLabels)
        elif isinstance(component, ConstComponent):
            return component
        elif isinstance(component, Variable):
            if component.label not in values:
                return component
            else:
                val = values[component.label]
                label = component.label if keepLabels else str(val)
                return Constant(label, val)

    @staticmethod
    def _combineUsedVariables(components):
        res = []
        for component in components:
            if isinstance(component, Variable):
                res.append(component)
            elif isinstance(component, Expression):
                res.extend(component.usedVariables)

        return tuple(res)
    
class TestResult:
    def __init__(self, prod, values):
        self.prod = prod
        self.values = values

    def __str__(self):
        return f"{tuple(self.prod.values())} {' | '.join(str(v) for v in self.values)}"
    
    def __repr__(self):
        return f"TestResult(prod={self.prod}, values={self.values})"

class Simulator:
    
    @staticmethod
    def _printCell(s, width):
        print(f"{str(s):>{width}}", end = " ")

    @staticmethod
    def _createVariableLabel(usedVariables):
        return f"({', '.join(v.label for v in usedVariables)})"

    @staticmethod
    def do(*expressions, variableSequence=None, variableSorted=False):
        
        test = Simulator(*expressions, variableSequence=variableSequence, variableSorted=variableSorted)

        widths = []

        vl = Simulator._createVariableLabel(test.usedVariables)
        print(vl, end=" ")

        widths.append(len(vl))

        for label in test.labels:
            print(label, end=" ")
            widths.append(len(label))

        print()

        for result in test.testResult:
            Simulator._printCell("(" + ", ".join(str(v) for v in result.prod.values()) + ")", widths[0])
            for value, width in zip(result.values, widths[1:]):
                Simulator._printCell(value, width)
            print()

        return test

    @staticmethod
    def doT(*expressions, variableSequence=None, variableSorted=False):
        
        test = Simulator(*expressions, variableSequence=variableSequence, variableSorted=variableSorted)
        
        widths = []

        vl = Simulator._createVariableLabel(test.usedVariables)
        width = max(len(lab) for lab in [Simulator._createVariableLabel(test.usedVariables), *test.labels])
        
        Simulator._printCell(vl, width)

        widths.append(width)

        for prod in test.prods:
            cell = "(" + ", ".join(str(v) for v in prod.values()) + ")"
            print(cell, end=" ")
            widths.append(len(cell))

        print()

        for i, label in enumerate(test.labels):
            Simulator._printCell(label, widths[0])

            for result, width in zip(test.testResult, widths[1:]):
                Simulator._printCell(result.values[i], width)
            print()

        return test

    def __init__(self, *expressions, variableSequence=None, variableSorted=False):
        self.expressions = expressions

        self.labels = [expression.label for expression in expressions]
        self.usedVariables = tuple(dict.fromkeys(
            var for exp in expressions for var in exp.usedVariables
        ))

        if variableSequence is not None:
            if set(self.usedVariables) != set(variableSequence):
                raise ValueError("사용된 변수들의 중복없는 튜플이 필요합니다.")
            self.usedVariables = variableSequence
        
        if variableSorted:
            self.usedVariables = tuple(sorted(self.usedVariables, key=lambda v: v.label))

        self.prods = self._makeProds()
        self.testResult = self._test()

    def _makeProds(self):
        def getProdWithVariable(variable, prev):
            if isinstance(variable, VariableComponent):
                return tuple([{**prev, variable.label: val} for val in (0, 1)])
            elif isinstance(variable, ConstComponent):
                return ({**prev, variable.label: variable.value}, )
            return (prev,)

        prod = [{}]
        for variable in self.usedVariables:
            prod = [pwv for p in prod for pwv in getProdWithVariable(variable, p)]

        return prod

    def _test(self):
        return tuple([TestResult(p, tuple(exp(**p).value for exp in self.expressions)) for p in self.prods])

if __name__ == "__main__":
    
    a = Variable("a")
    b = Variable("b")
    c = Variable("c")
    d = Variable("d")
    e = Variable("e")
    f = Variable("f")

    O = Constant("1", 1)

    X = a.nand(b.nand(c))
    Y = (a.nand(b)).nand(c)
    Simulator.doT(X, Y, variableSorted=True)

    print()

    A = a^b^c
    A1 = a^(b^c)
    B = a.nxor(b).nxor(c)
    B1 = a.nxor(b.nxor(c))
    C = (a^b).nxor(c)
    C1 = a^(b.nxor(c))
    D = (a.nxor(b))^c
    D1 = (a.nxor(b^c))

    Simulator.doT(A,A1,B,B1,C,C1,D,D1, variableSorted=True)

    print()

    Simulator.doT(a.nand(b.nand(c)), a.nand(b).nand(c), Component.nand_n(a, b, c))

    print()

    Simulator.doT(Component.xor_n(a, b), Component.nxor(a, b))

    print()

    Simulator.doT(Component.xor_n(a, b, c), a.nxor(b.nxor(c)))

    print()

    Simulator.do(Component.xor_n(a, b, c, d), a.nxor(b.nxor(c.nxor(d))))

    print()

    Simulator.do(Component.xor_n(a, b, c, d, e), a.nxor(b.nxor(c.nxor(d.nxor(e)))))

    print(a == c)