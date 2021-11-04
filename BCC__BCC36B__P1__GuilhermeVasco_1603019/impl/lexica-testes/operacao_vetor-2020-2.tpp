{A função preenche o vetor com valores}
preeenche_vetor(inteiro: vetor[], inteiro: tamanho) 
  inteiro: indice := 0

  repita
    se indice > 2 então
      vetor[indice] := -indice
    senão
      vetor[indice] := indice
    fim
    indice += 1
  até indice >= tamanho
fim

{A função processa o vetor}
processa_vetor(inteiro: vetor[], inteiro: tamanho) 
  inteiro: indice := 0
  inteiro: resultado := 0

  repita
    se vetor[indice] > 0 então
      resultado += vetor[indice]
    senão
      resultado -= 1
    fim
    indice += 1
  até indice >= tamanho

  retorna(resultado)
fim

inteiro: principal() 
  inteiro: tamanho := 5
  inteiro: vetor[tamanho]

  preeenche_vetor(vetor, tamanho)

  inteiro: resultado := processa_vetor(vetor, tamanho)

  escreva(resultado)

  retorna(0)
fim
