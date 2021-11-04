verifica (inteiro: n, inteiro: tam, inteiro: i)
	repita
		se n[i]<0
			escreva(n[i])
		fim
	até i=tam-1
fim

inteiro principal()
	inteiro: n[2]
	inteiro: i	
	inteiro: tam
	tam:=2
	
	n[0]:=0
	n[1]:=1	
	i:=0

	verifica(n, tam, i)

	return(0)
fim
