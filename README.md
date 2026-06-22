# GATE
논리회로 게이트 진리표 확인용 프로젝트입니다.  
파이썬 코드로 부울 함수를 정의하고 비교하며, 진리표 출력과 카르노 맵을 통한 간략화를 수행할 수 있습니다.

## 핵심 기능
- **부울 함수 정의**: 파이썬 연산자 오버라이딩(+, *, ~ ^ 등)과 nand, nor 등의 사전 정의 함수를 통한 손쉬운 부울 함수 정의
- **부울 함수 생성**: 부울 함수의 결과값 또는 최소항/최대항 번호를 통한 SOP, POS 표준형 자동 생성 
- **간략화**: 카르노 맵을 통한 2~4변수 부울 함수 간략화
- **비교**: 여러 수식이 같은지/다른지/보수관계인지, 같은/다른 경우의 변수 조합 출력
- **진리표**: 부울 함수 진리표 출력

## 클래스
- `Component`: 가장 기본적인 연산 단위. 식별자 `label: str`을 가지고 있습니다.
    - `ConstComponent`: 고정된 값을 가진 단위. 값 `value: boolValue` 을 가지고 있습니다.
        - `Constant`: 상수
        - `EvaluatedResult`: 대입이 완료되어 값이 계산된 수식
    - `VariableComponent`: 대입가능한 단위.
        - `Variable`: 변수
        - `Expression`: Component를 연산하여 얻어진 수식
## 변수 생성 방법
```python
# Variable(Label: str)
a = Variable("a")
b = Variable("b")

a2 = Variable("a")
# Label이 같은 변수는 같은 변수로 취급됩니다. 즉, a와 a2는 같은 변수입니다.
```

## 상수 생성 방법
기본적으로 정수 0, 1을 상수로 사용할 수 있습니다.  
Label이 있는 상수는 다음과 같이 생성할 수 있습니다.  

```python
O = Constant("O", 0)
I = Constant("I", 1)
```

## 수식 생성 방법
수식은 변수들과 0, 1을 연산하여 생성할 수 있습니다.

### 기본 연산
기본적인 NOT, AND, OR 등의 연산을 지원합니다. 반환값은 `Expression`입니다.
|연산 예시|설명|Label|
|---|---|---|
|`~a`|not 연산|a'|
|`a * b` <br> `a & b`|and 연산|(a·b)|
|`a + b` <br> `a \| b`|or 연산|(a+b)|
|`a ^ b`|xor 연산|(a⊕b)|
|`a.nand(b)`|nand 연산|(a·b)'|
|`a.nor(b)`|nor 연산|(a+b)'|
|`a.nxor(b)`|nxor 연산|(a⊙b)|
|`Component.and_n(a, b, ...)`|다중 입력 and 연산|(a·b·...)|
|`Component.or_n(a, b, ...)`|다중 입력 or 연산|(a+b+...)|
|`Component.xor_n(a, b, ...)`|다중 입력 xor 연산|(a⊕b⊕...)|
|`Component.nand_n(a, b, ...)`|다중 입력 nand 연산|(a·b·...)'|
|`Component.nor_n(a, b, ...)`|다중 입력 nor 연산|(a+b+...)'|
|`Component.nxor_n(a, b, ...)`|다중 입력 nxor 연산|(a⊕b⊕...)'|

연산의 결과를 다시 연산할 수 있습니다.
```python
F = a + 1 # (a+1)
G = F * c  # ((a+1)·c)

H = (a + 1) * (c ^ d) # ((a+1)·(c⊕d))
```

### 고급 연산

#### SOP 생성
1. `Component.SOP(*products: tuple[Variable, ...])` 
    - 곱(and)한 뒤 합(or) 연산을 수행합니다.
    - ```python
        Component.SOP((a, b), (c, d)) # ((a·b)+(c·d))
        ```

2. `Component.makeCanonicalSOP(*terms: int, variables: tuple[Variable, ...] | None = None) -> Expression`
    - 결과로부터 표준형 SOP를 반환합니다.
    - `variables = None` 이면 a-z 순서의 변수를 자동 생성합니다.
    - ```python
        Component.makeCanonicalSOP(0, 1, 1, 0, variables=(a, b)) # ((a'·b)+(a·b'))
        ```
    > term의 길이는 $2^{\text{len(variables)}}$ 여야 합니다.
3. `Component.fromMintermIndices(*indices: int, variables: tuple[Variable, ...]) -> Expression`
    - 항 번호로부터 표준형 SOP를 반환합니다.
    - ```python
        Component.fromMintermIndices(1, 2, variables=(a, b))         # ((a'·b)+(a·b'))
        ```
    > 항 번호는 최소 $0$, 최대 $2^{\text{len(variables)}} - 1$ 이여야 합니다.

#### POS 생성
SOP와 유사하게 `Component.POS`, `Component.makeCanonicalPOS`, `Component.fromMaxtermIndices` 함수를 지원합니다.  
사용법 또한 같습니다.

### 간략화
생성된 `Expression`은 `simplify` 메서드를 통해 간략화 할 수 있습니다.  
**karnaugh Map** 방식으로 간략화 되며, 2~4 변수의 수식만 간략화 가능합니다.  
`mode` 매개변수를 통해 SOP방식과 POS방식을 선택할 수 있습니다. 기본값은 `"SOP"`입니다.

```python
F = Component.SOP((a, b, c), (a, c), (b, c))

simplified_SOP = F.simplify(mode="SOP") # ((b·c)+(a·c))
# SOP는 기본값이므로 mode="SOP"는 생략 가능.

simplified_POS = F.simplify(mode="POS") # ((a+b)·(c))
```

### 대입
- `Component`에 값을 대입하여 결과를 확인할 수 있습니다.  
- `Component.__call__` 메서드로 값을 대입할 수 있습니다.  
- 이 때 `keepLabels` 매개변수를 통해 대입이 완료된 `Component`의 라벨을 유지할 지 설정할 수 있습니다. 기본값은 `False`입니다.

**`Variable`, `Constant`에 값을 대입하는 경우**
- `Constant`를 반환합니다.
- ```python
    v = Variable("v")
    O = Constant("O", 0)

    v(0) # 0
    v(1) # 1

    v(0, keepLabels=True) # v (v는 값이 0인 상수임.)
    v(1, keepLabels=True) # v (v는 값이 1인 상수임.)

    O() # 0
    O(keepLabels=True) # O (O는 값이 0인 상수임.)
    ```

**생성된 Expression에 값을 대입하는 경우**  
- 값 대입 방식은 순서 대입과 키워드 대입 두개가 있습니다.  
- 모든 변수에 대한 값을 한번에 줄 수도 있고 일부 변수 값만 줄 수 도 있습니다.
1. 모든 변수에 값 대입하기  
    - 모든 변수의 대입이 완료되면 `EvaluatedResult`를 반환합니다. 

    - ```python
        F = a + b

        result0 = F(1, 0) # (1+0) = 1
        result1 = F(a=1, b=0) # (1+0) = 1

        result2 = F(1, 0, keepLabels=True) # (a+b) = 1
        result3 = F(a=1, b=0, keepLabels=True) # (a+b) = 1
        ```
2. 일부 변수에 값 대입하기
    - 일부 변수에만 값을 대입할 수 있습니다.
    - 해당 변수에만 값이 대입된 `Expression`을 반환합니다.
    - ```python
        F = a + b

        result0 = F(1) # (1+b)

        result1 = F(b=0) # (a+0)

        result2 = F(1, keepLabels=True) # (a+b) (a는 값이 1인 상수임.)
        result3 = F(b=0, keepLabels=True) # (a+b) (b는 값이 0인 상수임.)

        # 남은 변수에 마저 대입
        evaluated0 = result0(0) # (1+0) = 1
        evaluated1 = result1(1) # (1+0) = 1
        evaluated2 = result2(0, keepLabels=True) # (a+b) = 1
        evaluated3 = result3(1, keepLabels=True) # (a+b) = 1
        ```
- 순서대로 대입은 권장하지 않습니다. 다음과 같이 의도와는 다른 결과가 발생할 수 있습니다.
- ```python
    F = (b + a)
    F(1, 0)
    # 의도: a=1, b=0이 대입된 (0 + 1) = 1
    # 결과: a=0, b=1이 대입된 (1 + 0) = 1

    F(a=1, b=0) # 키워드 대입을 통해 해결 가능
    ```
**`EvaluatedResult`에 값을 대입하는 경우**
- `keepLabels=False`(기본값): `Constant`를 반환합니다.
- `keepLabels=True`: 자기자신(`EvaluatedResult`)을 반환합니다.
- ```python
    evaluated = (a + b)(0, 1)

    evaluated() # 1
    evaluated(keepLabels=True) # (0+1) = 1
    ```
### 그 외 함수
- `toFuncStyle`
    - 생성된 `Expression`에서 `toFuncStyle(funcName: str)` 메서드를 통해 함수형태의 문자열을 생성할 수 있습니다. `funcName`의 기본값은 `"F"`입니다.
    - ```python
        (a+b).toFuncStyle() # F(a, b) = (a+b)
        (a+b).toFuncStyle("G") # G(a, b) = (a+b)
        ```

## `Component` 비교 및 진리표 출력
`Simulator`를 통해 `Component`들을 비교하고 진리표를 출력할 수 있습니다.  
`Simulator(*components: Component | boolValue, variableSequence: tuple[Variable, ...] | None = None, variableSorted: bool = False)` 로 생성합니다.
- `components`: 비교할 `Component`들입니다.
- `variableSequence`: `Component`에 사용된 변수 목록입니다. 설정하지 않으면 첫번째 `Component`의 변수부터 자동으로 인식합니다.
- `variableSorted`: 변수 정렬 여부입니다. `True`로 설정시 변수 `label`을 기준으로 사전순으로 정렬합니다. 기본값은 `False`입니다.

|속성/메서드|타입/반환값|설명|
|---|---|---|
|`simulator.testResults`|tuple[TestResult, ...]|각 경우(`prod={변수1: 값, 변수2: 값,...}`)에 따른 `components`들의 값(`values=(component1 값, component2 값, ...)`) 정보가 담긴 `TestResult`의 튜플을 반환합니다.|
|`simulator.case.same`|`tuple[VariableProd, ...]`|수식의 값이 같은 경우를 `{변수1: 값, 변수2: 값, ...}` 딕셔너리의 튜플로 반환합니다.|
|`simulator.case.different`|`tuple[VariableProd, ...]`|수식의 값이 다른 경우를 `{변수1: 값, 변수2: 값, ...}` 딕셔너리의 튜플로 반환합니다.|
|`simulator.caseTuple.same`|`tuple[tuple[boolValue, ...], ...]`|수식의 값이 같은 경우를 `(변수1 값, 변수2 값, ...)` 튜플의 튜플로 반환합니다.|
|`simulator.caseTuple.different`|`tuple[tuple[boolValue, ...], ...]`|수식의 값이 다른 경우를 `(변수1 값, 변수2 값, ...)` 튜플의 튜플로 반환합니다.|
|`simulator.isEqual`|`bool`|수식이 모든 경우에서 같으면 `True`를, 아니면 `False`를 반환합니다.|
|`simulator.isComplement`|`bool \| None`|수식이 보수 관계이면 `True`를, 아니면 `False`를 반환합니다. `components` 가 두개일 때만 비교가능하며 그 외에는 `None`을 반환합니다.|
|`simulator.printTruthTable()`|`None`|진리표를 출력합니다.|
|`simulator.printTransposedTruthTable()`|`None`|행과 열이 바뀐 진리표를 출력합니다.|
```python
simulator0 = Simulator(a + b, a * b)

simulator0.testResults # (TestResult(prod={'a': 0, 'b': 0}, values=(0, 0)), TestResult(prod={'a': 0, 'b': 1}, values=(1, 0)), TestResult(prod={'a': 1, 'b': 0}, values=(1, 0)), TestResult(prod={'a': 1, 'b': 1}, values=(1, 1)))
simulator0.case.same # ({'a': 0, 'b': 0}, {'a': 1, 'b': 1})
simulator0.case.different # ({'a': 0, 'b': 1}, {'a': 1, 'b': 0})
simulator0.caseTuple.same # ((0, 0), (1, 1))
simulator0.caseTuple.different # ((0, 1), (1, 0))
simulator0.isEqual # False
simulator0.isComplement # False

simulator0.printTruthTable()
"""
(a, b) (a+b) (a·b) 
(0, 0)     0     0 
(0, 1)     1     0 
(1, 0)     1     0 
(1, 1)     1     1 
"""

simulator0.printTransposedTruthTable()
"""
(a, b) (0, 0) (0, 1) (1, 0) (1, 1) 
 (a+b)      0      1      1      1 
 (a·b)      0      0      0      1 
"""
```
```python
simulator1 = Simulator(c + a, d + b, variableSequence=(a, b, c, d))
simulator2 = Simulator(c + a, d + b, variableSorted=True)
# 위의 경우처럼 변수들의 등장 순서가 뒤죽박죽일 경우 variableSequence 또는 variableSorted를 사용하여 정렬할 수 있습니다.
```