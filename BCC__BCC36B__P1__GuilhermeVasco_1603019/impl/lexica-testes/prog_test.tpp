flutuante: A[5]

inteiro inverteVetor()
	inteiro: i
	inteiro: n
	inteiro: aux
	
	i := 0
	n := 4
	
	repita
		aux := A[i]
		A[i] := A[n]
		A[n] := aux
		i := i + 1
		n := n - 1
	até i = n

	retorna(0)
fim

inteiro principal()	
	inteiro: i
	inteiro: n

	repita
		leia(n)
		A[i] := n
		i := i + 1
	até i = 5

	inverteVetor()

	i := 0

	repita
		escreva(A[i])
	até i = 5

	retorna(0)
fim