from __future__ import annotations
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any, Literal
import math

import random

def reduce[T, U](func: Callable[[U, T], U], iterable: Iterable[T], initial: U | None = None) -> U:
    it = iter(iterable)
    if initial is not None:
        acc = initial
    else:
        try:
            acc = next(it)
        except StopIteration:
            raise TypeError("비어있는 iterable에는 initial(초깃 값)이 필요합니다.") from None

    for v in it:
        acc = func(acc, v)
    return acc

class Operator:
    def __init__(self, name: str, handler: Callable[..., int], createLabel: Callable[..., str]):
        self.name = name
        self.handler = handler
        self.createLabel = createLabel

    def __call__(self, *args: int) -> int:
        return self.handler(*args)

AND = Operator('AND', lambda *x: int(all(x)), lambda *x: f"({'·'.join(x)})")
NAND = Operator('NAND', lambda *x: int(not all(x)), lambda *x: f"({'·'.join(x)})'")

OR = Operator('OR', lambda *x: int(any(x)), lambda *x: f"({'+'.join(x)})")
NOR = Operator('NOR', lambda *x: int(not any(x)), lambda *x: f"({'+'.join(x)})'")

XOR = Operator('XOR', lambda *x: int(reduce(lambda x1, x2: x1 ^ x2, x)), lambda *x: f"({'⊕ '.join(x)})")
NXOR = Operator('NXOR', lambda *x: int(1 - reduce(lambda x1, x2: x1 ^ x2, x)), lambda *x: f"({x[0]}⊙ {x[1]})" if len(x) == 2 else f"({'⊕ '.join(x)})'")

NOT = Operator("NOT", lambda x: int(not x), lambda x: f"{x}'")

type boolValue = Literal[0, 1]

type VariableProd = dict[str, boolValue]
type KMap = tuple[tuple[boolValue, ...], ...]

type GroupopedCells = set[tuple[int, int]]
type GroupopedKMap = tuple[tuple[tuple[GroupopedCells, ...], ...], ...]

class Component:
    def __init__(self, label: str, usedVariables: tuple[Variable, ...] | None = None) -> None:
        self._label = label
        self._usedVariables = usedVariables or tuple()

    @property
    def usedVariables(self) -> tuple[Variable, ...]:
        return self._usedVariables

    @property
    def label(self) -> str:
        return self._label
    
    def __call__(self, *args: int, keepLabels: bool = False, **kargs: int) -> Component:
        raise NotImplementedError("Component를 상속한 클래스는 __call__() 매소드를 구현해야 합니다.")

    def __str__(self) -> str:
        return self.label

    def __invert__(self) -> Expression:
        return Expression(NOT, self)

    def __mul__(self, other: Component | boolValue) -> Expression:
        return Expression(AND, self, other)
    
    def __rmul__(self, other: Component | boolValue) -> Expression:
        return Expression(AND, other, self)
    
    def __and__(self, other: Component | boolValue) -> Expression:
        return self.__mul__(other)
    
    def __rand__(self, other: Component | boolValue) -> Expression:
        return self.__rmul__(other)
    
    def __add__(self, other: Component | boolValue) -> Expression:
        return Expression(OR, self, other)
    
    def __radd__(self, other: Component | boolValue) -> Expression:
        return Expression(OR, other, self)

    def __or__(self, other: Component | boolValue) -> Expression:
        return self.__add__(other)

    def __ror__(self, other: Component | boolValue) -> Expression:
        return self.__radd__(other)
    
    def __xor__(self, other: Component | boolValue) -> Expression:
        return Expression(XOR, self, other)

    def __rxor__(self, other: Component | boolValue) -> Expression:
        return Expression(XOR, other, self)

    def nand(self, other: Component | boolValue) -> Expression:
        return Expression(NAND, self, other)
    
    def nor(self, other: Component | boolValue) -> Expression:
        return Expression(NOR, self, other)
    
    def nxor(self, other: Component | boolValue) -> Expression:
        return Expression(NXOR, self, other)
    
    @staticmethod
    def and_n(*components: Component | boolValue) -> Expression:
        return Expression(AND, *components)

    @staticmethod
    def nand_n(*components: Component | boolValue) -> Expression:
        return Expression(NAND, *components)
    
    @staticmethod
    def or_n(*components: Component | boolValue) -> Expression:
        return Expression(OR, *components)

    @staticmethod
    def nor_n(*components: Component | boolValue) -> Expression:
        return Expression(NOR, *components)
    
    @staticmethod
    def xor_n(*components: Component | boolValue) -> Expression:
        return Expression(XOR, *components)
    
    @staticmethod
    def nxor_n(*components: Component | boolValue) -> Expression:
        return Expression(NXOR, *components)
    
    @staticmethod
    def SOP(*products: tuple[Variable, ...]):
        return Component.or_n(*(Component.and_n(*variables) for variables in products))
    
    @staticmethod
    def POS(*sums: tuple[Variable, ...]):
        return Component.and_n(*(Component.or_n(*variables) for variables in sums))
    
    @staticmethod
    def makeCanonicalSOP(*terms: int, variables: tuple[Variable, ...] | None = None) -> Expression:
        
        variables = Component._convertVariables(terms, variables)
        prods = Component._makeProds(variables)

        minterms = []
        for idx, term in enumerate(terms):
            if not term:
                continue

            prod = prods[idx]
            minterms.append(
                Component.and_n(*(v if prod[v.label] else ~v for v in variables))
            )

        return Component.or_n(*minterms)
    
    @staticmethod
    def makeCanonicalPOS(*terms: int, variables: tuple[Variable, ...] | None = None) -> Expression:

        variables = Component._convertVariables(terms, variables)
        prods = Component._makeProds(variables)

        maxterms = []
        for idx, term in enumerate(terms):
            if term:
                continue

            prod = prods[idx]
            maxterms.append(
                Component.or_n(*(~v if prod[v.label] else v for v in variables))
            )

        return Component.and_n(*maxterms)
    
    @staticmethod
    def fromMintermIndices(*indices: int, variables: tuple[Variable, ...]) -> Expression:
        maxIndices = max(indices)

        indicesLimit = (1 << len(variables))
        if maxIndices >= indicesLimit:
            raise ValueError(f"항 번호는 2^(변수 수) - 1 = 2^{len(variables)} - 1 = {indicesLimit - 1}을(를) 초과할 수 없습니다.")

        indicesSet = set(indices)
        terms = (1 if i in indicesSet else 0 for i in range(indicesLimit))

        return Component.makeCanonicalSOP(*terms, variables=variables)
    
    @staticmethod
    def fromMaxtermIndices(*indices: int, variables: tuple[Variable, ...]) -> Expression:
        maxIndices = max(indices)

        indicesLimit = (1 << len(variables))
        if maxIndices >= indicesLimit:
            raise ValueError(f"항 번호는 2^(변수 수) - 1 = 2^{len(variables)} - 1 = {indicesLimit - 1}을(를) 초과할 수 없습니다.")

        indicesSet = set(indices)
        terms = (0 if i in indicesSet else 1 for i in range(indicesLimit))

        return Component.makeCanonicalPOS(*terms, variables=variables)

    @staticmethod
    def _convertVariables(terms: tuple[int, ...], variables: tuple[Variable, ...] | None):
        termsCount = len(terms)
        if variables:
            variableCount = len(variables)
            requiredCount = (1 << variableCount)
            if termsCount != requiredCount:
                raise ValueError(f"2^(변수 수) = 2^{variableCount} = {requiredCount} 길이의 terms이 필요합니다.(전달된 terms 길이: {termsCount})")
            
            return variables
        else:
            variableCount = Component._checkPowerOfTwo(termsCount)
            if variableCount == -1:
                raise ValueError("항의 수는 2의 n제곱 이여야 합니다.")
            
            return tuple(Variable(label) for label in "abcdefghijklmnopqrstuvwxyz"[:variableCount])
        
    @staticmethod
    def _checkPowerOfTwo(a: int) -> int:
        if a > 0 and (a & (a-1)) == 0:
            return round(math.log2(a))
        return -1

    @staticmethod
    def _makeProds(variables: tuple[Variable, ...]) -> tuple[VariableProd, ...]:
        labels = [v.label for v in variables]

        n = len(variables)
        prod = []
        for i in range(1 << n):
            prod.append({labels[j]: (i >> (n - 1 -j )) & 1 for j in range(n)})

        return tuple(prod)

    @staticmethod
    def _toComponent(value: Component | boolValue) -> Component:
        if isinstance(value, int):
            return Constant(str(int(bool(value))), int(bool(value)))
        elif isinstance(value, Component):
            return value
        
        raise TypeError(f"지원하지 않는 타입입니다: {type(value).__name__}. 'int' 또는 Component 타입만 가능합니다.")
    
    @staticmethod
    def _toComponents(values: Iterable[Component | boolValue]) -> tuple[Component, ...]:
        return tuple(Component._toComponent(v) for v in values)

class ConstComponent(Component):
    def __init__(self, label: str, value: int) -> None:
        super().__init__(label)
        self._value: boolValue = int(bool(value))
    
    @property
    def value(self) -> int:
        return self._value

    def __call__(self, *args: int, keepLabels: bool = False, **kargs: int) -> Component:
        return self if keepLabels else Constant(str(self.value), self.value)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(label={self.label}, value={self.value})"
    
    def toEquationStyle(self) -> str:
        return f"{self.label} = {self.value}"

class Constant(ConstComponent):
    pass
    
class EvaluatedResult(ConstComponent):
    def __str__(self):
        return f"{self.label} = {self.value}"

class VariableComponent(Component):

    def _toValuesDict(self, args: tuple[int, ...], kargs: VariableProd) -> VariableProd:
        if args and kargs:
            raise TypeError("위치 인자와 키워드 인자를 동시 사용할 수 없습니다. F(0, 0) 또는 F(a=0, b=0) 형태로 통일이 필요합니다.")

        if args:
            return dict(zip((v.label for v in self.usedVariables), args))
        return kargs

    @staticmethod
    def _resolve(component: Component, valuesDict: VariableProd, keepLabels: bool) -> Component:
        if isinstance(component, Expression):
            return component(**valuesDict, keepLabels=keepLabels)
        elif isinstance(component, ConstComponent):
            return component(keepLabels=keepLabels)
        elif isinstance(component, Variable):
            if component.label not in valuesDict:
                return component
            else:
                val = valuesDict[component.label]
                label = component.label if keepLabels else str(val)
                return Constant(label, val)

class Variable(VariableComponent):

    def __init__(self, label: str) -> None:
        super().__init__(label, (self, ))

    def __repr__(self) -> str:
        return f"Variable(label={self.label})"
    
    def __call__(self, *args: int, keepLabels: bool = False, **kargs: int) -> Component:
        valuesDict = self._toValuesDict(args, kargs)

        return self._resolve(self, valuesDict, keepLabels)

class Expression(VariableComponent):
    def __init__(self, operator: Operator, *terms: Component | boolValue) -> None:
        mappedTerms = Component._toComponents(terms)

        super().__init__(None, tuple(dict.fromkeys(var for com in mappedTerms for var in com.usedVariables)))

        self.operator = operator
        self.terms = mappedTerms

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(label={self.label}, variables=({', '.join(v.label for v in self.usedVariables)}))"

    @property
    def label(self) -> str:
        return self.operator.createLabel(*(term.label for term in self.terms))

    def __call__(self, *args: int, keepLabels: bool = False, **kargs: int) -> Component:

        valuesDict = self._toValuesDict(args, kargs)

        terms = [self._resolve(term, valuesDict, keepLabels) for term in self.terms]

        if any(v.label not in valuesDict for v in self.usedVariables):
            return Expression(self.operator, *terms)

        return EvaluatedResult(
            self.operator.createLabel(*(term.label for term in terms)),
            self.operator(*(term.value for term in terms))
        )

    def toFuncStyle(self, funcName="F") -> str:
        return f"{funcName}({', '.join(v.label for v in self.usedVariables)}) = {self.label}"
    
    def simplify(self, mode: Literal["SOP", "POS"] = "SOP") -> Expression:

        simulator = Simulator(self)

        terms = [re.values[0] for re in simulator.testResults]

        return Simplifier._simplify(
            terms, self.usedVariables, int(mode == "SOP")
        )

class TestResult:
    def __init__(self, prod: VariableProd, values: tuple[int, ...]) -> None:
        self.prod = prod
        self.values = values

    def __str__(self) -> str:
        return f"{tuple(self.prod.values())} {' | '.join(str(v) for v in self.values)}"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(prod={self.prod}, values={self.values})"
    
@dataclass(frozen=True)
class ComparisonResult:
    same: tuple[VariableProd, ...]
    different: tuple[VariableProd, ...]
    variables: tuple[Variable, ...]
    
@dataclass(frozen=True)
class ComparisonTupleResult:
    same: tuple[tuple[boolValue, ...], ...]
    different: tuple[tuple[boolValue, ...], ...]
    variables: tuple[Variable, ...]

class Simplifier:
    
    @staticmethod
    def _toKMap(terms: tuple[Literal[0, 1], ...]) -> KMap:
        re = Component._checkPowerOfTwo(len(terms))

        if re == -1 or re < 2 or re > 4:
            raise ValueError("terms의 길이는 2의 n제곱이여야합니다.(n=2,3,4)")

        if re == 2:
            colCount = 2
            rowCase = (0, 1)
            colCase = (0, 1)
        elif re == 3:
            colCount = 4
            rowCase = (0, 1)
            colCase = (0, 1, 3, 2)
        elif re == 4:
            colCount = 4
            rowCase = (0, 1, 3, 2)
            colCase = (0, 1, 3, 2)

        return tuple(tuple(terms[i * colCount + j] for j in colCase) for i in rowCase)
    
    @staticmethod    
    def _groupKMap(karnaughMap: KMap, target: Literal[0, 1]) -> GroupopedKMap:

        rowCount = len(karnaughMap)
        colCount = len(karnaughMap[0])

        pi = tuple([tuple() for _ in range(colCount)] for _ in range(rowCount))

        ZOHAP = {
            16: ((4, 4), ),
            8: ((4, 2), (2, 4)),
            4: ((4, 1), (1, 4), (2, 2)),
            2: ((2, 1), (1, 2)),
            1: ((1, 1), )
        }

        for zohap in ZOHAP.values():
            for kernelX, kernelY in zohap:

                if rowCount < kernelX or colCount < kernelY:
                    continue


                for i in range(1 if kernelX == rowCount else rowCount):
                    for j in range(1 if kernelY == colCount else colCount):

                        isSameWithTarget = True
                        hangs = set()
                        for x in range(kernelX):
                            if not isSameWithTarget:
                                break

                            for y in range(kernelY):
                                realX = (i + x) % rowCount
                                realY = (j + y) % colCount
                                if karnaughMap[realX][realY] != target:
                                    isSameWithTarget = False
                                    break

                                hangs.add((realX, realY))

                        if not isSameWithTarget:
                            continue

                        for x in range(kernelX):
                            for y in range(kernelY):
                                ta = pi[(i + x) % rowCount][(j + y) % colCount]

                                if any(hangs <= v for v in ta):
                                    continue

                                pi[(i + x) % rowCount][(j + y) % colCount] += (hangs, )
        return tuple(tuple(p for p in o) for o in pi)

    @staticmethod
    def _getEPI(groupopedKM: GroupopedKMap) -> tuple[GroupopedCells, ...]:

        epis = []
        for i in range(len(groupopedKM)):
            for j in range(len(groupopedKM[0])):
                s = groupopedKM[i][j]

                if len(s) == 1 and s[0] not in epis:
                    epis.append(s[0])

        return tuple(epis)

    @staticmethod
    def _getEPIRemovedKM(piList: GroupopedKMap, epis: tuple[GroupopedCells, ...]) -> GroupopedKMap:

        newGKM = tuple([tuple() for _ in range(len(piList[0]))] for _ in range(len(piList)))
        for i in range(len(piList)):
            for j in range(len(piList[0])):
                s = piList[i][j]

                if not s:
                    continue

                if any(x in epis for x in s):
                    continue
                
                newGKM[i][j] = piList[i][j]
        return tuple(tuple(p for p in o) for o in newGKM)

    @staticmethod
    def _selectPI(epiRemovedList: GroupopedKMap) -> tuple[GroupopedCells, ...]:
        flattenPis = [c for a in epiRemovedList for b in a for c in b]

        d = {} # pi항의 길이: pi[] 딕셔너리
        for pi in flattenPis:
            length = len(pi)
            pi_tuple = tuple(sorted(pi))

            if length not in d:
                d[length] = []
            d[length].append(pi_tuple)

        for length, piList in d.items():
            counts = {item: piList.count(item) for item in set(piList)}
            d[length] = list(pi for pi, count in sorted(counts.items(), key=lambda x: x[1]))

        sortedAllPis = dict(sorted(d.items(), reverse=True))
        # length가 큰 순서대로 정렬

        dd = {} # pi: 항번호[] 딕셔너리
        colCount = len(epiRemovedList[0])
        for i, gap in enumerate(epiRemovedList):
            for j, g in enumerate(gap):
                if not g:
                    continue

                for pi in g:
                    k = tuple(sorted(pi))
                    if k not in dd:
                        dd[k] = []
                    dd[k].append(i * colCount + j)

        selectedPis = []
        selectedHangs = set()
        for length, piss in sortedAllPis.items():
            for my in random.sample(piss, len(piss)):
                if my in selectedPis:
                    continue
                usedHangs = dd[my]
                if all(hang in selectedHangs for hang in usedHangs):
                    continue
                selectedPis.append(my)
                selectedHangs.update(usedHangs)

        return tuple(selectedPis)

    @staticmethod
    def _combineCells(cells: GroupopedCells, variables: tuple[Variable, ...], target: Literal[0, 1]) -> Expression:
        sonsur = ((0, 0), (0, 1), (1, 1), (1, 0))
        variableCount = len(variables)
        variableCase = [[] for _ in range(variableCount)]

        if variableCount == 2:
            for x, y in cells:
                variableCase[0].append(x)
                variableCase[1].append(y)
        elif variableCount == 3:
            for x, y in cells:
                a = sonsur[y]
                variableCase[0].append(x)
                variableCase[1].append(a[0])
                variableCase[2].append(a[1])
        elif variableCount == 4:
            for x, y in cells:
                a = sonsur[x]
                b = sonsur[y]
                variableCase[0].append(a[0])
                variableCase[1].append(a[1])
                variableCase[2].append(b[0])
                variableCase[3].append(b[1])

        terms = []
        for i, v in enumerate(variableCase):
            first = v[0]
            if all(z == first for z in v):
                if first == target:
                    terms.append(variables[i])
                else:
                    terms.append(~variables[i])
        return Component.and_n(*terms) if target == 1 else Component.or_n(*terms)

    @staticmethod
    def _operatePis(pis: tuple[GroupopedCells, ...], variables: tuple[Variable, ...], target: Literal[0, 1]):
        if target == 1:
            return Component.or_n(*(Simplifier._combineCells(pi, variables, 1) for pi in pis))
        else:
            return Component.and_n(*(Simplifier._combineCells(pi, variables, 0) for pi in pis))

    @staticmethod
    def _simplify(terms: tuple[Literal[0, 1], ...], variables: tuple[Variable, ...], target: Literal[0, 1]) -> Expression:
        grouppedKM = Simplifier._groupKMap(
                        Simplifier._toKMap(terms),
                        target
                    )
        
        epis = Simplifier._getEPI(grouppedKM)
        selectedPis = Simplifier._selectPI(
                        Simplifier._getEPIRemovedKM(grouppedKM, epis)
                    )
        
        return Simplifier._operatePis(epis + selectedPis, variables, target)

class Simulator:

    def __init__(self, *components: Component | boolValue, variableSequence: tuple[Variable, ...] | None = None, variableSorted: bool = False) -> None:

        mappedComponents = Component._toComponents(components)

        self.components: tuple[Component, ...] = mappedComponents

        self.labels: tuple[str, ...] = tuple(expression.label for expression in mappedComponents)

        self.usedVariables: tuple[Variable, ...] = tuple(dict.fromkeys(
            var for exp in mappedComponents for var in exp.usedVariables
        ))

        if variableSequence is not None:
            if set(self.usedVariables) != set(variableSequence):
                raise ValueError("전달된 variableSequence가 수식의 변수 목록과 일치하지 않습니다.")
            self.usedVariables = variableSequence

        if variableSorted:
            self.usedVariables = tuple(sorted(self.usedVariables, key=lambda v: v.label))

        self.prods: tuple[VariableProd, ...] = Component._makeProds(self.usedVariables)
        self.testResults: tuple[TestResult, ...] = self._test()

        self.case: ComparisonResult = self._findCase()
        self.caseTuple: ComparisonTupleResult = self._findCase(True)

        self.isEqual: bool = self._isEqual()
        
        self.isComplement: bool | None = self._isComplement() if len(mappedComponents) == 2 else None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(components={self.components})"
    
    def _test(self) -> tuple[TestResult, ...]:
        return tuple(
            TestResult(
                p, tuple(
                    exp(**p).value
                    for exp in self.components
                )
            )
            for p in self.prods
        )
    
    def printTruthTable(self) -> None:

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

    def printTransposedTruthTable(self) -> None:
        
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

    def _findCase(self, toTuple: bool = False) -> ComparisonResult | ComparisonTupleResult:

        equalCases = []
        differentCases = []

        for res in self.testResults:
            prod = tuple(res.prod.values()) if toTuple else res.prod
            if len(set(res.values)) == 1:
                equalCases.append(prod)
            else:
                differentCases.append(prod)

        if toTuple:
            return ComparisonTupleResult(same=tuple(equalCases), different=tuple(differentCases), variables=self.usedVariables)
        else:
            return ComparisonResult(same=tuple(equalCases), different=tuple(differentCases), variables=self.usedVariables)
        
    def _isEqual(self) -> bool:
        return all(len(set(res.values)) == 1 for res in self.testResults)

    def _isComplement(self) -> bool:
        if(len(self.components) != 2):
            raise TypeError("두 요소를 가진 Simulator만 보수 판정을 할 수 있습니다.")

        return all(len(set(res.values)) == 2 for res in self.testResults)

    @staticmethod
    def _printCell(s: Any, width: int) -> None:
        print(f"{str(s):>{width}}", end = " ")

    @staticmethod
    def _createVariableLabel(usedVariables: Iterable[Variable]) -> str:
        return f"({', '.join(v.label for v in usedVariables)})"