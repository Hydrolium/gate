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

x = Variable("x")
y = Variable("y")
z = Variable("z")
w = Variable("w")

O = Constant("O", 0)

# # X = a.nand(b.nand(c))
# # Y = (a.nand(b)).nand(c)
# # Simulator.printTruthTable(X, Y, variableSorted=True)

# Simulator(O).printTruthTable()

# print()

# A0 = Component.xor_n(a, b, c)
# A = a^b^c
# A1 = a^(b^c)

# B0 = Component.nxor_n(a, b, c)
# B = a.nxor(b).nxor(c)
# B1 = a.nxor(b.nxor(c))
# C = (a^b).nxor(c)
# C1 = a^(b.nxor(c))
# D = (a.nxor(b))^c
# D1 = (a.nxor(b^c))

# Simulator(A0, A, A1, B0, B, B1, C, C1, D, D1, variableSorted=True).printTransposedTruthTable()

# print()

# Simulator(a.nand(b.nand(c)), a.nand(b).nand(c), Component.nand_n(a, b, c)).printTransposedTruthTable()

# print()

# # n 변수에서 xor과 nxor 인지 확인
# vals = [Variable(l) for l in "abcdefghijkl"]
# for i in range(2, len(vals) + 1):
#     curV = vals[:i]
#     F1 = Component.xor_n(*curV)
#     F2 = curV[0]
#     for v in curV[1:]:
#         F2 = F2.nxor(v)

#     print(f"(변수 수) = {len(curV):<2} 에서 XOR과 NXOR 연산은 ", end="")
#     simulator = Simulator(F1, F2)
#     if simulator.isEqual:
#         print("같음.")
#     if simulator.isComplement:
#         print("보수임.")

# print(Component.and_n(1, 1, 1).toFuncStyle())
# print(Component.and_n(1, 1, a).toFuncStyle())
# print(Component.and_n(1, 1, 1)())

# print()

# X = a + b

# simulator = Simulator(X, O)

# simulator.printTruthTable()

# print("사용된 변수들:", "(" + ", ".join(v.label for v in simulator.caseTuple.variables) + ")")

# print(X.toFuncStyle("F"), "=", O, "이 되는 경우:", simulator.caseTuple.same)
# print(X.toFuncStyle("G"), "≠", O, "이 되는 경우:", simulator.caseTuple.different)

# print()

# print(simulator)

# x = a*b
# y = x + ~b
# z = (~b).nor(c)

# F = y.nand(z)

# Simulator(x, y, z, F).printTruthTable()

# F_0_SOP = Component.or_n(
#     Component.and_n(a, ~b, ~c),
#     Component.and_n(a, ~c, d),
#     Component.and_n(a, c, ~d),
#     Component.and_n(b, c, ~d),
#     Component.and_n(~a, ~b, c, d)
# ) 

# F_0_POS = Component.and_n(
#     Component.or_n(a, c),
#     Component.or_n(a, b, d),
#     Component.or_n(a, ~b, ~d),
#     Component.or_n(~a, ~c, ~d),
#     Component.or_n(~a, ~b, c, d),
# )

# Simulator(F_0_SOP, F_0_POS).printTruthTable()


# F_2_SOP = Component.or_n(
#     Component.and_n(a, b),
#     Component.and_n(b, ~c, d),
#     Component.and_n(~a, ~b, c, d)
# ) 

# F_2_POS = Component.and_n(
#     Component.or_n(~a, b),
#     Component.or_n(a, d),
#     Component.or_n(b, c),
#     Component.or_n(a, ~b, ~c),
# )

# Simulator(F_2_SOP, F_2_POS).printTruthTable()
# print(Simulator(F_2_SOP, F_2_POS).isEqual)

# F_3_SOP = Component.or_n(
#     Component.and_n(b, ~d),
#     Component.and_n(~c, ~d)
# ) 

# F_3_POS = Component.and_n(
#     Component.or_n(~d),
#     Component.or_n(b, ~c)
# )

# Simulator(F_3_SOP, F_3_POS).printTruthTable()
# print(Simulator(F_3_SOP, F_3_POS).isEqual)

# F_4_SOP = Component.or_n(
#     Component.and_n(a, b),
#     Component.and_n(a, ~d),
#     Component.and_n(a, ~c),
#     Component.and_n(~a, ~b, c, d)
# ) 

# SOP2 = Component.SOP((a, b), (a, ~d), (a, ~c), (~a, ~b, c, d))

# F_4_POS = Component.and_n(
#     Component.or_n(a, ~b),
#     Component.or_n(a, c),
#     Component.or_n(a, d),
#     Component.or_n(~a, b, ~c, ~d)
# )


# Simulator(F_4_POS, POS2).printTruthTable()
# print(Simulator(F_4_POS, POS2).isEqual)

# Simulator(a, b ^ (c+d), variableSorted=True).printTruthTable()



# Simulator(a*b, a + ~b, b * ~c, ).printTruthTable()


# F = Component.makeCanonicalSOP(1, 0, 0, 1, 1, 0, 0, 1, variables=(a, b, d))
# F2 = Component.makeCanonicalPOS(1, 0, 0, 1, 1, 0, 0, 1, variables=(a, b, d))



# simpd = F.simplify()
# print(simpd)

# simpd2 = F2.simplify()
# print(simpd2)

F3 = a + b + c
print(F3.simplify("SOP"))
