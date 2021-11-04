inteiro escalar(inteiro : array1[], inteiro : array2[], inteiro : n)
  inteiro : produto
  produto := 0
  inteiro : i
  i := 0
  se n > 0 entao
    repita
      produto := produto + array1[i] * array2[i]
      i := i + 1
    ate i = n
  retorna (produto)
fim