paraBinario(inteiro: n) 

    inteiro: N[32]; 
  
    inteiro: i
    
    para i := 0 até n > 0 faça

        N[i] := n%2
        n := n/2 
        
    fim

    inteiro: j
    j := i -1 

    repita

        escreva(N[j])
        j := j -1 

    até j < 0

fim 
  
inteiro principal() 
    inteiro : num

    leia(num)
    paraBinario(num) 

fim