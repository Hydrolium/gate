class Operator:
    def __init__(self, name, handler, createLabel):
        self.name = name
        self.handler = handler
        self.createLabel = createLabel

    def __call__(self, *args):
        return self.handler(*args)

AND = Operator('AND', lambda *x: int(all(x)), lambda *x: f"({'·'.join(x)})")
NAND = Operator('NAND', lambda *x: int(not all(x)), lambda *x: f"({'·'.join(x)})'")

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
    
    def __str__(self):
        return self.label

    def __invert__(self):
        return Expression(NOT, self)

    def __mul__(self, other):
        return Expression(AND, self, self._toComponent(other))
    
    def __rmul__(self, other):
        return Expression(AND, self._toComponent(other), self)
    
    def __and__(self, other):
        return self.__mul__(other)
    
    def __rand__(self, other):
        return self.__rmul__(other)
    
    def __add__(self, other):
        return Expression(OR, self, self._toComponent(other))
    
    def __radd__(self, other):
        return Expression(OR, self._toComponent(other), self)

    def __or__(self, other):
        return self.__add__(other)

    def __ror__(self, other):
        return self.__radd__(other)
    
    def __xor__(self, other):
        return Expression(XOR, self, self._toComponent(other))

    def __rxor__(self, other):
        return Expression(XOR, self._toComponent(other), self)

    def nand(self, other):
        return Expression(NAND, self, self._toComponent(other))
    
    def nor(self, other):
        return Expression(NOR, self._toComponent(other))
    
    def nxor(self, other):
        return Expression(NXOR, self, self._toComponent(other))
    
    @staticmethod
    def and_n(*components):
        return Expression(AND, *Component._toComponents(components))

    @staticmethod
    def nand_n(*components):
        return Expression(NAND, *Component._toComponents(components))
    
    @staticmethod
    def or_n(*components):
        return Expression(OR, *Component._toComponents(components))

    @staticmethod
    def nor_n(*components):
        return Expression(NOR, *Component._toComponents(components))
    
    @staticmethod
    def xor_n(*components):
        return Expression(XOR, *Component._toComponents(components))
    
    @staticmethod
    def _toComponent(value):
        if isinstance(value, int):
            return Constant(str(int(bool(value))), int(bool(value)))
        elif isinstance(value, Component):
            return value
        
        raise TypeError(f"지원하지 않는 타입입니다: {type(value).__name__}. 'int' 또는 'Component' 타입만 가능합니다.")
    
    @staticmethod
    def _toComponents(values):
        return tuple(Component._toComponent(v) for v in values)
    
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
    
    @classmethod
    def printTruthTable(cls, *expressions, variableSequence=None, variableSorted=False):
        
        test = cls(*expressions, variableSequence=variableSequence, variableSorted=variableSorted)

        widths = []

        vl = cls._createVariableLabel(test.usedVariables)
        print(vl, end=" ")

        widths.append(len(vl))

        for label in test.labels:
            print(label, end=" ")
            widths.append(len(label))

        print()

        for result in test.testResults:
            cls._printCell("(" + ", ".join(str(v) for v in result.prod.values()) + ")", widths[0])
            for value, width in zip(result.values, widths[1:]):
                cls._printCell(value, width)
            print()

        return test

    @classmethod
    def printTransposedTruthTable(cls, *expressions, variableSequence=None, variableSorted=False):
        
        test = cls(*expressions, variableSequence=variableSequence, variableSorted=variableSorted)
        
        widths = []

        vl = cls._createVariableLabel(test.usedVariables)
        width = max(len(lab) for lab in [cls._createVariableLabel(test.usedVariables), *test.labels])
        
        cls._printCell(vl, width)

        widths.append(width)

        for prod in test.prods:
            cell = "(" + ", ".join(str(v) for v in prod.values()) + ")"
            print(cell, end=" ")
            widths.append(len(cell))

        print()

        for i, label in enumerate(test.labels):
            cls._printCell(label, widths[0])

            for result, width in zip(test.testResults, widths[1:]):
                cls._printCell(result.values[i], width)
            print()

        return test
    
    @classmethod
    def findCase(cls, *expressions, variableSequence=None, variableSorted=False, toTuple=False):

        if not Simulator._isUsingSameVariables(expressions):
            raise ValueError("같은 변수를 사용한 수식들만 비교할 수 있습니다.")

        test = cls(*expressions, variableSequence=variableSequence, variableSorted=variableSorted)

        equalCases = []
        differentCases = []

        for res in test.testResults:
            prod = tuple(res.prod.values()) if toTuple else res.prod
            if len(set(res.values)) == 1:
                equalCases.append(prod)
            else:
                differentCases.append(prod)

        return tuple(equalCases), tuple(differentCases)
    
    @classmethod
    def isEqual(cls, *expressions, variableSequence=None, variableSorted=False):

        if not Simulator._isUsingSameVariables(expressions):
            raise ValueError("같은 변수를 사용한 수식들만 비교할 수 있습니다.")
        test = cls(*expressions, variableSequence=variableSequence, variableSorted=variableSorted)

        return all(len(set(res.values)) == 1 for res in test.testResults)

    @classmethod
    def isComplement(cls, expression0, expression1, variableSequence=None, variableSorted=False):

        if not Simulator._isUsingSameVariables((expression0, expression1)):
            raise ValueError("같은 변수를 사용한 수식들만 비교할 수 있습니다.")

        test = cls(expression0, expression1, variableSequence=variableSequence, variableSorted=variableSorted)
        return all(len(set(res.values)) == 2 for res in test.testResults)


    def __init__(self, *expressions, variableSequence=None, variableSorted=False):
        self.expressions = expressions

        self.labels = [expression.label for expression in expressions]
        self.usedVariables = tuple(dict.fromkeys(
            var for exp in expressions for var in exp.usedVariables
        ))

        if variableSequence is not None:
            if set(self.usedVariables) != set(variableSequence):
                raise ValueError("전달된 variableSequence가 수식의 변수 목록과 일치하지 않습니다.")
            self.usedVariables = variableSequence
        
        if variableSorted:
            self.usedVariables = tuple(sorted(self.usedVariables, key=lambda v: v.label))

        self.prods = self._makeProds()
        self.testResults = self._test()

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
        return tuple(TestResult(p, tuple(exp(**p).value for exp in self.expressions)) for p in self.prods)
    
    @staticmethod
    def _printCell(s, width):
        print(f"{str(s):>{width}}", end = " ")

    @staticmethod
    def _createVariableLabel(usedVariables):
        return f"({', '.join(v.label for v in usedVariables)})"
    
    @staticmethod
    def _isUsingSameVariables(expressions):
        variables = set(expressions[0].usedVariables)
        return all(set(exp.usedVariables) == variables for exp in expressions)

if __name__ == "__main__":

    a = Variable("a")
    b = Variable("b")
    c = Variable("c")
    d = Variable("d")
    e = Variable("e")
    f = Variable("f")
    g = Variable("g")
    h = Variable("h")
    i = Variable("i")
    j = Variable("j")
    k = Variable("k")
    l = Variable("l")

    O = Constant("1", 1)

    X = a.nand(b.nand(c))
    Y = (a.nand(b)).nand(c)
    Simulator.printTruthTable(X, Y, variableSorted=True)

    print()

    A = a^b^c
    A1 = a^(b^c)
    B = a.nxor(b).nxor(c)
    B1 = a.nxor(b.nxor(c))
    C = (a^b).nxor(c)
    C1 = a^(b.nxor(c))
    D = (a.nxor(b))^c
    D1 = (a.nxor(b^c))

    Simulator.printTruthTable(A,A1,B,B1,C,C1,D,D1, variableSorted=True)

    print()

    Simulator.printTransposedTruthTable(a.nand(b.nand(c)), a.nand(b).nand(c), Component.nand_n(a, b, c))

    print()

    # n 변수에서 xor과 nxor 인지 확인
    vals = [a, b, c, d, e, f, g, h, i, j, k, l]
    for i in range(2, len(vals) + 1):
        curV = vals[:i]
        F1 = Component.xor_n(*curV)
        F2 = curV[0]
        for v in curV[1:]:
            F2 = F2.nxor(v)

        print(f"(변수 수) = {len(curV)} 에서 XOR과 NXOR 연산은 ", end="")
        if Simulator.isEqual(F1, F2):
            print("같음.")
        if Simulator.isComplement(F1, F2):
            print("보수임.")

    print(Component.and_n(1, 1, a))

    print()