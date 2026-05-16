def reduce(func, iterable, inital=None):
    it = iter(iterable)
    acc = inital or next(it)

    for v in it:
        acc = func(acc, v)
    return acc

class Operator:
    def __init__(self, name, handler, createLabel):
        self.name = name
        self.handler = handler
        self.createLabel = createLabel

    def __call__(self, *args):
        return self.handler(*args)

AND = Operator('AND', lambda *x: int(all(x)), lambda *x: f"({'·'.join(x)})")
NAND = Operator('NAND', lambda *x: int(not all(x)), lambda *x: f"({'·'.join(x)})'")

OR = Operator('OR', lambda *x: int(any(x)), lambda *x: f"({'+'.join(x)})")
NOR = Operator('NOR', lambda *x: int(not any(x)), lambda *x: f"({'+'.join(x)})'")

XOR = Operator('XOR', lambda *x: int(reduce(lambda x1, x2: x1 != x2, x)), lambda *x: f"({'⊕ '.join(x)})")
NXOR = Operator('NXOR', lambda *x: int(not reduce(lambda x1, x2: x1 != x2, x)), lambda *x: f"({x[0]}⊙ {x[1]})" if len(x) == 2 else f"({'⊕ '.join(x)})'")

NOT = Operator("NOT", lambda x: int(not x), lambda x: f"{x}'")

class Component:
    def __init__(self, label, usedVariables=tuple()):
        self._label = label
        self._usedVariables = usedVariables

    @property
    def usedVariables(self):
        return self._usedVariables

    @property
    def label(self):
        return self._label
    
    def __call__(self, *args, keepLabels=False, **kargs):
        raise NotImplementedError("Component를 상속한 클래스는 __call__() 매소드를 구현해야 합니다.")

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
    def nxor_n(*components):
        return Expression(NXOR, *Component._toComponents(components))

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

class ConstComponent(Component):
    def __init__(self, label, value):
        super().__init__(label)
        self._value = int(bool(value))
    
    @property
    def value(self):
        return self._value

    def __call__(self, *args, keepLabels=False, **kargs):
        return self

    def __str__(self):
        return str(self.value)
    
    def __repr__(self):
        return f"{self.__class__.__name__}(label={self.label}, value={self.value})"
    
    def toEquationStyle(self):
        return f"{self.label} = {self.value}"

class Constant(ConstComponent):

    def __init__(self, label, value):
        if len(label) != 1:
            raise ValueError("Variable의 label은 길이가 1이여야합니다.")
        
        super().__init__(label, value)

class EvaluatedResult(ConstComponent):
    pass

class VariableComponent(Component):

    def _toValuesDict(self, args, kargs):
        if args and kargs:
            raise TypeError("위치 인자와 키워드 인자를 동시 사용할 수 없습니다. F(0, 0) 또는 F(a=0, b=0) 형태로 통일이 필요합니다.")

        if args:
            return dict(zip((v.label for v in self.usedVariables), args))
        return kargs

    @staticmethod
    def _resolve(component, valuesDict, keepLabels):
        if isinstance(component, Expression):
            return component(**valuesDict, keepLabels=keepLabels)
        elif isinstance(component, ConstComponent):
            return component
        elif isinstance(component, Variable):
            if component.label not in valuesDict:
                return component
            else:
                val = valuesDict[component.label]
                label = component.label if keepLabels else str(val)
                return Constant(label, val)

class Variable(VariableComponent):

    def __init__(self, label):
        if len(label) != 1:
            raise ValueError("Variable의 label은 길이가 1이여야합니다.")
        
        super().__init__(label, (self, ))

    def __repr__(self):
        return f"Variable(label={self.label})"
    
    def __call__(self, *args, keepLabels=False, **kargs):
        valuesDict = self._toValuesDict(args, kargs)

        return self._resolve(self, valuesDict, keepLabels)

class Expression(VariableComponent):
    def __init__(self, operator, *terms):
        super().__init__(None, tuple(dict.fromkeys(var for com in terms for var in com.usedVariables)))

        self.operator = operator
        self.terms = terms

    def __repr__(self):
        return f"Expression(label={self.label}, variables={', '.join(v.label for v in self.usedVariables)})"

    @property
    def label(self):
        return self.operator.createLabel(*(term.label for term in self.terms))

    def __call__(self, *args, keepLabels=False, **kargs):

        valuesDict = self._toValuesDict(args, kargs)

        terms = [self._resolve(term, valuesDict, keepLabels) for term in self.terms]

        if any(v.label not in valuesDict for v in self.usedVariables):
            return Expression(self.operator, *terms)

        return EvaluatedResult(
            self.operator.createLabel(*(term.label for term in terms)),
            self.operator(*(term.value for term in terms))
        )

    def toFuncStyle(self, funcName="F"):
        return f"{funcName}({', '.join(v.label for v in self.usedVariables)}) = {self.label}"


class TestResult:
    def __init__(self, prod, values):
        self.prod = prod
        self.values = values

    def __str__(self):
        return f"{tuple(self.prod.values())} {' | '.join(str(v) for v in self.values)}"
    
    def __repr__(self):
        return f"TestResult(prod={self.prod}, values={self.values})"

class Simulator:

    def __init__(self, *components, variableSequence=None, variableSorted=False):

        components = [Component._toComponent(exp) for exp in components]

        self.components = components

        self.labels = [expression.label for expression in components]
        self.usedVariables = tuple(dict.fromkeys(
            var for exp in components for var in exp.usedVariables
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
        labels = [v.label for v in self.usedVariables]

        n = len(self.usedVariables)
        prod = []
        for i in range(1 << n):
            prod.append({labels[j]: (i >> (n - 1 -j )) & 1 for j in range(n)})

        return tuple(prod)

    def _test(self):
        return tuple(
            TestResult(
                p, tuple(
                    exp(**p).value
                    for exp in self.components
                )
            )
            for p in self.prods
        )
    
    def printTruthTable(self):

        widths = []

        vl = self._createVariableLabel(self.usedVariables)
        print(vl, end=" ")

        widths.append(len(vl))

        for label in self.labels:
            print(label, end=" ")
            widths.append(len(label))

        print()

        for result in self.testResults:
            self._printCell("(" + ", ".join(str(v) for v in result.prod.values()) + ")", widths[0])
            for value, width in zip(result.values, widths[1:]):
                self._printCell(value, width)
            print()

    def printTransposedTruthTable(self):
        
        widths = []

        vl = self._createVariableLabel(self.usedVariables)
        width = max(len(lab) for lab in [vl, *self.labels])
        
        self._printCell(vl, width)

        widths.append(width)

        for prod in self.prods:
            cell = "(" + ", ".join(str(v) for v in prod.values()) + ")"
            print(cell, end=" ")
            widths.append(len(cell))

        print()

        for i, label in enumerate(self.labels):
            self._printCell(label, widths[0])

            for result, width in zip(self.testResults, widths[1:]):
                self._printCell(result.values[i], width)
            print()
    

    def findCase(self, toTuple=False):

        equalCases = []
        differentCases = []

        for res in self.testResults:
            prod = tuple(res.prod.values()) if toTuple else res.prod
            if len(set(res.values)) == 1:
                equalCases.append(prod)
            else:
                differentCases.append(prod)

        return {"same": tuple(equalCases), "different": tuple(differentCases), "variables": self.usedVariables}
    
    def isEqual(self):
        return all(len(set(res.values)) == 1 for res in self.testResults)

    def isComplement(self):
        if(len(self.components) != 2):
            raise TypeError("두 요소를 가진 Simulator만 보수 판정을 할 수 있습니다.")

        return all(len(set(res.values)) == 2 for res in self.testResults)

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