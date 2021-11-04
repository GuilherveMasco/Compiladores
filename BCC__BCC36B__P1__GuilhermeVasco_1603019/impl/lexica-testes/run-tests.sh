#!/bin/bash

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 lexer.py" >&2
  exit 1
fi

LEXER=$1

for f in `ls *.tpp`; do 
  echo Testing with $f
  python3 $LEXER $f > $f-test.out
  diff $f-test.out $f.out > $f.diff;  
done

echo "-------------------------------------------------"
echo "Relatório dos Testes: "
echo "-------------------------------------------------"

errors=0
num_test=0
for f in `ls *.diff`; do
  ((num_test=num_test+1))
  if [ -s $f ]
  then
    printf '%02d. Teste %-35s[NOK]\n' $num_test $f
    # echo Teste $f: [NOK]
    echo '     >>>' ocorreram `wc -l $f | cut -d' ' -f1` erros.
    ((errors=errors+1))
  else
    printf '%02d. Teste %-35s[OK]\n' $num_test $f
    # echo Teste $f: [OK].      
  fi
done

echo "-------------------------------------------------"
if [ $errors -gt 0 ]; then 
  echo '>>' $errors "Teste(s) falharam".
else
  echo 'OK'
fi
echo "-------------------------------------------------"
