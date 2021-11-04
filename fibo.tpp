inteiro: n

inteiro fib(inteiro: n)
	inteiro: i
	inteiro: fib1
	inteiro: fib2
	inteiro: soma
	i := 3
	fib1 := 1
	fib2 := 1
	se i <= n então
		soma := fib1 + fib2
		fib1 := fib2
		fib2 := soma
		i := i + 1
	senão
		retorna(fib2)
	fim
fim

inteiro principal()
	leia(n)
	fib(n)
	{ comentário }