{
	computa se um numero eh primos
}
inteiro: num

inteiro principal()
	inteiro: counter, primo
	leia(num)
	counter := 1
	primo := 1
	repita
		counter := counter + 1
		res := num - ((num/counter)*counter)
		escreva(res)
		se res = 0 então primo := 0 fim
	até counter = (num-1)

	escreva(primo)
	
	retorna(0)
fim
