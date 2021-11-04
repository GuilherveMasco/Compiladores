flutuante: A[10]

selectionSort(inteiro: n)
    flutuante: i
    flutuante: j
    flutuante: min
    flutuante: aux
    i:=0
    repita
        min:= i
        j:=i+1
        repita
            se A[j] < A[min]
                min:= j
            fim
            j:= j+1
        até j = n
        aux:= A[i]
        A[i]:= A[min]
        A[min]:= aux
        i:= i+1
    até i = n-1
fim

inteiro principal()
    A:=[2,1,3,9,5,7,6,8,4,0]
    selectionSort(10)
fim
