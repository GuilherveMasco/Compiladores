flutuante: a[100]
flutuante: b[100]
flutuante: c[100]


subtraiVetores(inteiro: n) 
	inteiro: i
	i := 0
	repita
		c[i] := a[i] - b[i]
		i := i + 1
	até i = n
fim


inteiro principal()
	inteiro: i
	i := 0
	repita
		a[i] := 200
		b[i] := 50
		i := i + 1
	até i = 100

	subtraiVetores(100)
	retorna 0
fim

