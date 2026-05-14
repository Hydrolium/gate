class Operator:
    def __init__(self, name, func, createLabel):
        self.name = name
        self.func = func
        self.createLabel = createLabel

AND = Operator('AND', lambda x, y: x and y, lambda x, y: f"({x}{y})") # ·
NAND = Operator('NAND', lambda x, y: not (x and y), lambda x, y: f"({x}{y})'")

OR = Operator('OR', lambda x, y: x or y, lambda x, y: f"({x}+{y})")
NOR = Operator('NOR', lambda x, y: not (x or y), lambda x, y: f"({x}+{y})'")

XOR = Operator('XOR', lambda x, y: x != y, lambda x, y: f"({x}⊕ {y})")
NXOR = Operator('NXOR', lambda x, y: x == y, lambda x, y: f"({x}⊙ {y})")

class Component:
    def __init__(self, label):
        self.label = label

    def __invert__(self):
        return ComplementExpression(self)

    def __mul__(self, other):
        if isinstance(other, (int, bool)):
            other = Constant(f"{other}", int(other))
        return Expression(self, other, AND)
    
    def __rmul__(self, other):
        if isinstance(other, (int, bool)):
            other = Constant(f"{other}", int(other))
        return Expression(other, self, AND)
    
    def __and__(self, other):
        return self.__mul__(other)
    
    def __rand__(self, other):
        return self.__rmul__(other)
    
    def __add__(self, other):
        if isinstance(other, (int, bool)):
            other = Constant(f"{other}", int(other))
        return Expression(self, other, OR)
    
    def __radd__(self, other):
        if isinstance(other, (int, bool)):
            other = Constant(f"{other}", int(other))
        return Expression(other, self, OR)

    def __or__(self, other):
        return self.__add__(other)

    def __ror__(self, other):
        return self.__radd__(other)
    
    def __xor__(self, other):
        if isinstance(other, (int, bool)):
            other = Constant(f"{other}", int(other))
        return Expression(self, other, XOR)

    def __rxor__(self, other):
        if isinstance(other, (int, bool)):
            other = Constant(f"{other}", int(other))
        return Expression(other, self, XOR)

    def nand(self, other):
        if isinstance(other, (int, bool)):
            other = Constant(f"{other}", int(other))
        return Expression(self, other, NAND)

    def nor(self, other):
        if isinstance(other, (int, bool)):
            other = Constant(f"{other}", int(other))
        return Expression(self, other, NOR)
    
    def nxor(self, other):
        if isinstance(other, (int, bool)):
            other = Constant(f"{other}", int(other))
        return Expression(self, other, NXOR)

    def __str__(self):
        return self.label
    
class VariableComponent(Component):
    pass

class ValuedComponent(Component):
    def __init__(self, label, value):
        super().__init__(label)
        self.value = int(value)

    def __str__(self):
        return f"{self.label} = {self.value}"

class Variable(VariableComponent):
    def __repr__(self):
        return f"Variable(label={self.label})"

class Constant(ValuedComponent):
    def __repr__(self):
        return f"Constant(label={self.label}, value={self.value})"

class Evaluated(ValuedComponent):
    def __init__(self, label, value, usedVariables):
        super().__init__(label, value)
        self.usedVariables = usedVariables

    def __repr__(self):
        return f"Constant(label={self.label}, value={self.value})"

class SubstitutableComponent(VariableComponent):

    @staticmethod
    def _flat(component, values):
        if isinstance(component, SubstitutableComponent):
            return component.substitute(values)
        elif isinstance(component, (Constant, Evaluated)):
            return component
        elif isinstance(component, Variable):
            if component.label not in values:
                return component
            else:
                return Constant(values[component.label], values[component.label])

    def substitute(self, values):
        raise NotImplementedError("substitute 매세드가 구현되지 않았습니다.")

    @staticmethod
    def _getUpdatedUsedVariables(variable, initialTuple):
        if isinstance(variable, Variable):
            return initialTuple + (variable,)
        elif isinstance(variable, (Expression, Evaluated, ComplementExpression)):
            return initialTuple + (*variable.usedVariables,)
        
        return initialTuple

class ComplementExpression(SubstitutableComponent):
    def __init__(self, variable):
        super().__init__(f"{variable.label}'")
        self.variable = variable

        self.usedVariables = tuple(dict.fromkeys(
            self._getUpdatedUsedVariables(variable, tuple())
        ))

    def substitute(self, values):
        flatVar = self._flat(self.variable, values)

        if not set(v.label for v in self.usedVariables).issubset(values):
            return ComplementExpression(flatVar)
        
        return Evaluated(
            f"{flatVar.label}'",
            int(not flatVar.value),
            self.usedVariables
        )
    
    def __repr__(self):
        return f"ComplementExpression(label={self.label})"

class Expression(SubstitutableComponent):
    def __init__(self, left, right, operator):
        super().__init__(None)

        self.left = left
        self.right = right
        self.operator = operator

        self.usedVariables = tuple(dict.fromkeys(
            self._getUpdatedUsedVariables(
                right, self._getUpdatedUsedVariables(
                    left, tuple()))))

    @property
    def label(self):
        return self.operator.createLabel(self.left.label, self.right.label)

    @label.setter
    def label(self, value):
        pass

    # values: {$variableLabel: $variableValue, ...}
    def substitute(self, values):

        flatLeft = self._flat(self.left, values)
        flatRight = self._flat(self.right, values)

        if not set(v.label for v in self.usedVariables).issubset(values):
            return Expression(flatLeft, flatRight, self.operator)
        
        return Evaluated(
            self.operator.createLabel(flatLeft.label, flatRight.label),
            self.operator.func(flatLeft.value, flatRight.value),
            self.usedVariables
        )

    def __repr__(self):
        return f"Expression(label={self.label})"
    
class TestResult:
    def __init__(self, prod, values):
        self.prod = prod
        self.values = values

    def __str__(self):
        return f"{tuple(self.prod.values())} {" | ".join([str(v) for v in self.values])}"
    
    def __repr__(self):
        return f"TestResult(prod={self.prod}, values={self.values}"

class Simulator:
    
    @staticmethod
    def _printCell(s, width):
        print(f"{str(s):>{width}}", end = " ")

    @staticmethod
    def _createVariableLabel(usedVariables):
        return f"({", ".join(v.label for v in usedVariables)})"

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

        if variableSequence != None:
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
            elif isinstance(variable, ValuedComponent):
                return ({**prev, variable.label: variable.value}, )
            
            return (prev,)

        prod = [{}]
        for variable in self.usedVariables:
            prod = [pwv for p in prod for pwv in getProdWithVariable(variable, p)]

        return prod

    def _test(self):
        return tuple([TestResult(p, tuple(exp.substitute(p).value for exp in self.expressions)) for p in self.prods])

if __name__ == "__main__":
    
    a = Variable("a")
    b = Variable("b")
    c = Variable("c")
    d = Variable("d")
    e = Variable("e")
    f = Variable("f")

    O = Constant("1", 1)

    # X = a.nand(b.nand(c))
    # Y = (a.nand(b)).nand(c)
    # Simulator.doT(X, Y, variableSorted=True)

    # print()

    A = a^b^c
    A1 = a^(b^c)
    B = a.nxor(b).nxor(c)
    B1 = a.nxor(b.nxor(c))
    C = (a^b).nxor(c)
    C1 = a^(b.nxor(c))
    D = (a.nxor(b))^c
    D1 = (a.nxor(b^c))

    Simulator.doT(A,A1,B,B1,C,C1,D,D1, variableSorted=True)

    print((~(a+b) + c).substitute({'a':1, 'c':0}))

"""
A NAND (B NAND C)
(A NAND B) NAND C

A XOR B XOR C
A NXOR B NXOR C
A XOR B NXOR C
A NXOR B XOR C

(a, b, c) (0, 0, 0) (0, 0, 1) (0, 1, 0) (0, 1, 1) (1, 0, 0) (1, 0, 1) (1, 1, 0) (1, 1, 1) 
(a(bc)')'         1         1         1         1         0         0         0         1 
((ab)'c)'         1         0         1         0         1         0         1         1 

  (a, b, c) (0, 0, 0) (0, 0, 1) (0, 1, 0) (0, 1, 1) (1, 0, 0) (1, 0, 1) (1, 1, 0) (1, 1, 1) 
((a⊕ b)⊕ c)         0         1         1         0         1         0         0         1 
(a⊕ (b⊕ c))         0         1         1         0         1         0         0         1 
((a⊙ b)⊙ c)         0         1         1         0         1         0         0         1 
(a⊙ (b⊙ c))         0         1         1         0         1         0         0         1 
((a⊕ b)⊙ c)         1         0         0         1         0         1         1         0 
(a⊕ (b⊙ c))         1         0         0         1         0         1         1         0 
((a⊙ b)⊕ c)         1         0         0         1         0         1         1         0 
(a⊙ (b⊕ c))         1         0         0         1         0         1         1         0 

"""