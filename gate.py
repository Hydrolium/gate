import pandas as pd

class Operator:
    def __init__(self, name, func, createLabel):
        self.name = name
        self.func = func
        self.createLabel = createLabel

AND = Operator('AND', lambda x, y: x and y, lambda x, y: f"({x}·{y})")
NAND = Operator('NAND', lambda x, y: not (x and y), lambda x, y: f"({x}{y})'")

OR = Operator('OR', lambda x, y: x or y, lambda x, y: f"({x}+{y})")
NOR = Operator('NOR', lambda x, y: not (x or y), lambda x, y: f"({x}+{y})'")

XOR = Operator('XOR', lambda x, y: x != y, lambda x, y: f"({x}⊕ {y})")
NXOR = Operator('NXOR', lambda x, y: x == y, lambda x, y: f"({x}⊙ {y})")

class Component:
    def __init__(self, label):
        self.label = label

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

    def __str__(self):
        return self.label
    
    def __repr__(self):
        return self.label
    
class VariableComponent(Component):
    pass

class ValuedComponent(Component):
    def __init__(self, label, value):
        super().__init__(label)
        self.value = int(value)

class Variable(VariableComponent):
    def __init__(self, label):
        super().__init__(label)

class Constant(ValuedComponent):
    pass

class Equation(ValuedComponent):
    def __init__(self, label, value, usedVariables):
        super().__init__(label, value)
        self.usedVariables = usedVariables

class Expression(VariableComponent):
    def __init__(self, left, right, operator):
        super().__init__(None)

        self.left = left
        self.right = right
        self.operator = operator

        self.usedVariables = []

        if isinstance(left, Variable):
            self.usedVariables.append(left)
        elif isinstance(left, (Expression, Equation)):
            self.usedVariables += left.usedVariables

        if isinstance(right, Variable):
            self.usedVariables.append(right)
        elif isinstance(right, (Expression, Equation)):
            self.usedVariables += right.usedVariables

        self.usedVariables = list(dict.fromkeys(self.usedVariables))

    @property
    def label(self):

        def flat(component):
            # if isinstance(component, (Expression, Constant, Equation, Variable)):
            return component.label
            
        leftLabel = flat(self.left)
        rightLabel = flat(self.right)

        return self.operator.createLabel(leftLabel, rightLabel)

    @label.setter
    def label(self, value):
        self._label = value

    # values: {$variableLabel: $variableValue, ...}
    def substitute(self, values):

        def flat(component):
            if isinstance(component, Expression):
                e = component.substitute(values)
                return e.label, e.value
            elif isinstance(component, (Constant, Equation)):
                return component.label, component.value
            elif isinstance(component, Variable):
                return component.label, values[component.label]
            
        leftLabel, leftValue = flat(self.left)
        rightLabel, rightValue = flat(self.right)

        return Equation(
            self.operator.createLabel(leftLabel, rightLabel),
            self.operator.func(leftValue, rightValue),
            self.usedVariables
        )
    

def makeProd(variables):

    def update(variable, prod, p={}):
        if isinstance(variable, VariableComponent):
            prod.append({**p, variable.label: 0})
            prod.append({**p, variable.label: 1})
        elif isinstance(variable, ValuedComponent):
            prod.append({**p, variable.label: variable.value})

    def mp(variable, previous):
        newProd = []

        if len(previous) == 0:
            update(variable, newProd)
            return tuple(newProd)

        for p in previous:
            update(variable, newProd, p)

        return tuple(newProd)

    labels = []
    prod = tuple()
    for variable in variables:
        labels.append(variable.label)
        prod = mp(variable, prod)

    return tuple(labels), prod

def test(expression, onlyResult=False):
    r = []

    labels, prod = makeProd(expression.usedVariables)
    print(f"({", ".join(labels)})", expression.label)
    for p in prod:
        result = expression.substitute(p)
        print(tuple(p.values()), end=" -> ")
        if onlyResult:
            print(result.label, "=", result.value)
            r.append((result.label, result.value))
        else:
            print(result.value)
            r.append(result.value)
    return r

def compare(*expressions, onlyResult=False):
    
    usedVariables = list(dict.fromkeys(sum(map(lambda x: x.usedVariables, expressions), [])))
    labels, prod = makeProd(usedVariables)

    print(f"({", ".join(labels)})", " | ".join(map(lambda expression: expression.label, expressions)))

    def createSubstitutedLabel(expression, p):
        result = expression.substitute(p)
        return f"{result.value}" if onlyResult else f"{result.label} = {result.value}"

    for p in prod:
        results = map(lambda x: createSubstitutedLabel(x, p), expressions)
        print(tuple(p.values()), end=" ")
        print(" | ".join(results))

a = Variable("a")
b = Variable("b")
c = Variable("c")
d = Variable("d")
e = Variable("e")
f = Variable("f")

v = test((a ^ b)*(c))
print(v)

compare(a+b, b+c, onlyResult=True)