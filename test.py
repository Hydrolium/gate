from gate import *

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

O = Constant("O", 0)

# X = a.nand(b.nand(c))
# Y = (a.nand(b)).nand(c)
# Simulator.printTruthTable(X, Y, variableSorted=True)

Simulator(O).printTruthTable()

print()

A0 = Component.xor_n(a, b, c)
A = a^b^c
A1 = a^(b^c)

B0 = Component.nxor_n(a, b, c)
B = a.nxor(b).nxor(c)
B1 = a.nxor(b.nxor(c))
C = (a^b).nxor(c)
C1 = a^(b.nxor(c))
D = (a.nxor(b))^c
D1 = (a.nxor(b^c))

Simulator(A0, A, A1, B0, B, B1, C, C1, D, D1, variableSorted=True).printTransposedTruthTable()

print()

Simulator(a.nand(b.nand(c)), a.nand(b).nand(c), Component.nand_n(a, b, c)).printTransposedTruthTable()

print()

# n 변수에서 xor과 nxor 인지 확인
vals = [Variable(l) for l in "abcdefghijklmn"]
for i in range(2, len(vals) + 1):
    curV = vals[:i]
    F1 = Component.xor_n(*curV)
    F2 = curV[0]
    for v in curV[1:]:
        F2 = F2.nxor(v)

    print(f"(변수 수) = {len(curV):<2} 에서 XOR과 NXOR 연산은 ", end="")
    simulator = Simulator(F1, F2)
    if simulator.isEqual():
        print("같음.")
    if simulator.isComplement():
        print("보수임.")

print(Component.and_n(1, 1, 1).toFuncStyle())
print(Component.and_n(1, 1, a).toFuncStyle())
print(Component.and_n(1, 1, 1)())

print()

X = a + b

simulator = Simulator(X, O)

simulator.printTruthTable()

ca = simulator.findCase(toTuple=True)
print("사용된 변수들:", "(" + ", ".join(v.label for v in ca["variables"]) + ")")

print(X.toFuncStyle("F"), "=", O, "이 되는 경우:", ca["same"])
print(X.toFuncStyle("G"), "≠", O, "이 되는 경우:", ca["different"])