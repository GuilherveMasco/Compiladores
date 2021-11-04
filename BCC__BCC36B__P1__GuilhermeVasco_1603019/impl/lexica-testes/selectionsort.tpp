selection_sort(inteiro[]: num, inteiro: tamanho) 
  inteiro: i
  inteiro: j
  inteiro: menor
  inteiro: auxiliar
  i := 0
  repita
    auxiliar := i
    repita
      se num[j] < num[auxiliar]
        auxiliar := j
      fim
      j := j + 1
    até j < tamanho
    menor := num[auxiliar]
    num[auxiliar] := num[i]
    num[i] = menor
    i := i + 1
  até i < (tam - 1)
fim