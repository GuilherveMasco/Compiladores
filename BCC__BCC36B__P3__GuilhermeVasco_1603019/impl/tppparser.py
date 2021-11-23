import ply.yacc as yacc
import logging
import graphviz

from mytree import MyNode
from anytree.exporter import DotExporter, UniqueDotExporter
from anytree import RenderTree, AsciiStyle
from sys import argv, exit
from copy import copy

import tppLex as tpplex

lexer_object = tpplex.tppLex()
tokens = lexer_object.tokens
lexer = lexer_object.build()

escopo = 'global'
func_list = dict()
var_list = dict()
message_list = list()

logging.basicConfig(
    level=logging.DEBUG,
    filename="sintatic.log",
    filemode="w",
    format="%(filename)10s:%(lineno)4d:%(message)s"
)
log = logging.getLogger()


# Funções auxiliares

def find_all_nodes(node, list_parameter, label):
    for sun in node.children:
        list_parameter = find_all_nodes(sun, list_parameter, label)

        if sun.label == label:
            list_parameter.append(sun)

    return list_parameter


def find_all_filter_nodes(node, label, father_label, list_node):
    all_nodes = find_all_nodes(node, label, list_node)

    i = 0
    len_list = len(all_nodes)

    while i < len_list:
        if all_nodes[i].ancestors[-1].label != father_label:
            all_nodes.pop(i)

            len_list -= 1
            i -= 1

        i += 1

    return all_nodes


def get_call_var(node, line, add=True):
    call_name_list = find_all_nodes(node, list(), 'ID')
    exist = False
    for call_name in call_name_list:
        if call_name.children[0].label in var_list:
            if add:
                var_list[call_name.children[0].label][-1][-1].append((line, node))
            exist = True
        else:
            if call_name.anchestors[-1].label != 'chamada_funcao':
                message = ('ERROR', f'Erro: Variável "{call_name.children[0].label}" não declarada.')
                message_list.append(message)

    return exist


def get_call_func(node, line, p):
    call_name_func = node.descendants[1].label

    if call_name_func in func_list:
        func_list[call_name_func][-1][-1].append((line, node))
    else:
        func_list[call_name_func] = [[call_name_func, '', 0, [], [], -1, -1, False, [(line, node)]]]


# Sub-árvore.
#       (programa)
#           |
#   (lista_declaracoes)
#     /     |      \
#   ...    ...     ...
def p_programa(p):
    """programa : lista_declaracoes"""

    global root

    programa = MyNode(name='programa', type='PROGRAMA')

    root = programa
    p[0] = programa
    p[1].parent = programa


#    (lista_declaracoes)                          (lista_declaracoes)
#          /           \                                    |
# (lista_declaracoes)  (declaracao)                    (declaracao)
def p_lista_declaracoes(p):
    """lista_declaracoes : lista_declaracoes declaracao
                        | declaracao
    """
    pai = MyNode(name='lista_declaracoes', type='LISTA_DECLARACOES')
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai


# Sub-árvore.
#      (declaracao)
#           |
#  (declaracao_variaveis ou  
#   inicializacao_variaveis ou 
#   declaracao_funcao)
def p_declaracao(p):
    """declaracao : declaracao_variaveis
                | inicializacao_variaveis
                | declaracao_funcao
    """
    pai = MyNode(name='declaracao', type='DECLARACAO')
    p[0] = pai
    p[1].parent = pai


# Sub-árvore.
#      (declaracao_variaveis)
#      / p[1]    |           \
# (tipo)    (DOIS_PONTOS)    (lista_variaveis)
#                |
#               (:)
def p_declaracao_variaveis(p):
    "declaracao_variaveis : tipo DOIS_PONTOS lista_variaveis"

    global escopo

    pai = MyNode(name='declaracao_variaveis', type='DECLARACAO_VARIAVEIS')
    p[0] = pai

    p[1].parent = pai

    filho = MyNode(name='dois_pontos', type='DOIS_PONTOS', parent=pai)
    filho_sym = MyNode(name=p[2], type='SIMBOLO', parent=filho)
    p[2] = filho

    p[3].parent = pai

    nodes_var = find_all_nodes(p.slice[-1].value, list(), 'ID')
    for node_var in nodes_var:
        name_var = node_var.children[0].label
        type_var = p.slice[1].value.children[0].children[0].label

        dimensions = find_all_nodes(p.slice[-1].value, list(), 'expressao')
        dimension_name = []

        if len(dimensions) > 0:
            for sun in dimensions:
                aux = find_all_nodes(sun, list(), 'numero')

                if len(aux) == 0:
                    aux = find_all_nodes(sun, list(), 'var')

                dimension_name.append((aux[-1].children[-1].children[-1].label, aux[-1].children[-1].label))

        if name_var in var_list:
            # message = ('WARNING', f'Aviso: Variável "{name_var}" já declarada anteriormente.')
            # message_list.append(message)
            var_list[name_var].append([name_var, type_var, len(dimensions), dimension_name, escopo, p.lineno(2), list()])
        else:
            var_list[name_var] = [[name_var, type_var, len(dimensions), dimension_name, escopo, p.lineno(2), list()]]


# Sub-árvore.
#   (inicializacao_variaveis)
#              |
#         (atribuicao)
def p_inicializacao_variaveis(p):
    "inicializacao_variaveis : atribuicao"

    pai = MyNode(name='inicializacao_variaveis', type='INICIALIZACAO_VARIAVEIS')
    p[0] = pai
    p[1].parent = pai


def p_lista_variaveis(p):
    """lista_variaveis : lista_variaveis VIRGULA var
                        | var
    """
    pai = MyNode(name='lista_variaveis', type='LISTA_VARIAVEIS')
    p[0] = pai
    if len(p) > 2:
        p[1].parent = pai
        filho = MyNode(name='virgula', type='VIRGULA', parent=pai)
        filho_sym = MyNode(name=',', type='SIMBOLO', parent=filho)
        p[3].parent = pai
    else:
        p[1].parent = pai


def p_var(p):
    """var : ID
            | ID indice
    """

    pai = MyNode(name='var', type='VAR')
    p[0] = pai
    filho = MyNode(name='ID', type='ID', parent=pai)
    filho_id = MyNode(name=p[1], type='ID', parent=filho)
    p[1] = filho
    if len(p) > 2:
        p[2].parent = pai


def p_indice(p):
    """indice : indice ABRE_COLCHETE expressao FECHA_COLCHETE
                | ABRE_COLCHETE expressao FECHA_COLCHETE
    """
    pai = MyNode(name='indice', type='INDICE')
    p[0] = pai
    if len(p) == 5:
        p[1].parent = pai  # indice

        filho2 = MyNode(name='abre_colchete', type='ABRE_COLCHETE', parent=pai)
        filho_sym2 = MyNode(name=p[2], type='SIMBOLO', parent=filho2)
        p[2] = filho2

        p[3].parent = pai  # expressao

        filho4 = MyNode(name='fecha_colchete', type='FECHA_COLCHETE', parent=pai)
        filho_sym4 = MyNode(name=p[4], type='SIMBOLO', parent=filho4)
        p[4] = filho4
    else:
        filho1 = MyNode(name='abre_colchete', type='ABRE_COLCHETE', parent=pai)
        filho_sym1 = MyNode(name=p[1], type='SIMBOLO', parent=filho1)
        p[1] = filho1

        p[2].parent = pai  # expressao

        filho3 = MyNode(name='fecha_colchete', type='FECHA_COLCHETE', parent=pai)
        filho_sym3 = MyNode(name=p[3], type='SIMBOLO', parent=filho3)
        p[3] = filho3


def p_indice_error(p):
    """indice : error ABRE_COLCHETE expressao FECHA_COLCHETE
                | indice ABRE_COLCHETE error FECHA_COLCHETE
                | ABRE_COLCHETE error FECHA_COLCHETE
    """
    global parser

    print("Erro na definicao do indice. Expressao ou indice.")

    print("Erro:p[0]:{p0}, p[1]:{p1}, p[2]:{p2}, p[3]:{p3}".format(p0=p[0], p1=p[1], p2=p[2], p3=p[3]))
    error_line = p.lineno(2)
    father = MyNode(name='ERROR::{}'.format(error_line), type='ERROR')
    logging.error(
        "Syntax error parsing index rule at line {}".format(error_line))
    parser.errok()
    p[0] = father
    # if len(p) == 4:
    #     p[1] = new_node('ABRECOLCHETES', father)
    #     p[2].parent = father
    #     p[3] = new_node('FECHACOLCHETES', father)
    # else:
    #     p[1].parent = father
    #     p[2] = new_node('ABRECOLCHETES', father)
    #     p[3].parent = father
    #     p[4] = new_node('FECHACOLCHETES', father)


# Sub-árvore:
#    (tipo)
#      |
#  (FLUTUANTE)
def p_tipo(p):
    """tipo : INTEIRO
        | FLUTUANTE
    """

    pai = MyNode(name='tipo', type='TIPO')
    p[0] = pai
    # p[1] = MyNode(name=p[1], type=p[1].upper(), parent=pai)

    if p[1] == "inteiro":
        filho1 = MyNode(name='INTEIRO', type='INTEIRO', parent=pai)
        filho_sym = MyNode(name=p[1], type=p[1].upper(), parent=filho1)
        p[1] = filho1
    else:
        filho1 = MyNode(name='FLUTUANTE', type='FLUTUANTE', parent=pai)
        filho_sym = MyNode(name=p[1], type=p[1].upper(), parent=filho1)


def p_declaracao_funcao(p):
    """declaracao_funcao : tipo cabecalho 
                        | cabecalho 
    """
    pai = MyNode(name='declaracao_funcao', type='DECLARACAO_FUNCAO')
    p[0] = pai
    p[1].parent = pai

    if len(p) == 3:
        p[2].parent = pai


def p_cabecalho_error(p):
    """cabecalho : ID error lista_parametros FECHA_PARENTESE corpo FIM
                | ID ABRE_PARENTESE lista_parametros error corpo FIM
                | ID ABRE_PARENTESE lista_parametros FECHA_PARENTESE corpo 
    """
    global parser

    print("Erro na definicao do cabeçalho. Lista de parâmetros ou corpo.")

    print(f"Erro:p[0]:{p[0]}, p[1]:{p[1]}, p[2]:{p[2]}, p[3]:{p[3]}, p[4]:{p[4]}, p[5]:{p[5]}")
    error_line = p.lineno(2)
    father = MyNode(name=f'ERROR::{error_line}', type='ERROR')
    logging.error(f"Syntax error parsing index rule at line {error_line}")
    parser.errok()
    p[0] = father


def p_cabecalho(p):
    """cabecalho : ID ABRE_PARENTESE lista_parametros FECHA_PARENTESE corpo FIM"""
    global escopo

    # Nome da função
    name_func = p.slice[1].value

    pai = MyNode(name='cabecalho', type='CABECALHO')
    p[0] = pai

    filho1 = MyNode(name='ID', type='ID', parent=pai)
    filho_id = MyNode(name=p[1], type='ID', parent=filho1)
    p[1] = filho1

    filho2 = MyNode(name='abre_parentese', type='ABRE_PARENTESE', parent=pai)
    filho_sym2 = MyNode(name='(', type='SIMBOLO', parent=filho2)
    p[2] = filho2

    p[3].parent = pai  # lista_parametros

    filho4 = MyNode(name='fecha_parentese', type='FECHA_PARENTESE', parent=pai)
    filho_sym4 = MyNode(name=')', type='SIMBOLO', parent=filho4)
    p[4] = filho4

    p[5].parent = pai  # corpo

    filho6 = MyNode(name='FIM', type='FIM', parent=pai)
    filho_id = MyNode(name='fim', type='FIM', parent=filho6)
    p[6] = filho6

    # Tipo da função
    if p.stack[-1].value.children[0].label == 'INTEIRO':
        type_func = 'inteiro'
    elif p.stack[-1].value.children[0].label == 'FLUTUANTE':
        type_func = 'flutuante'
    else:
        type_func = 'vazio'

    # Numero de parâmetros e o nome dos parâmetros
    list_parameter = find_all_nodes(p.slice[3].value, list(), 'parametro')
    num_var = len(list_parameter)

    name_parameter = []
    for parameter in list_parameter:
        name_parameter.append(find_all_nodes(parameter, list(), 'ID')[0].children[0].label)

    line_start = p.lineno(2)
    line_end = p.slice[-1].lineno

    for element in var_list:
        for var in var_list[element]:
            if line_start <= var[-2] < line_end:
                var[4] = name_func

    # Tipos de Retorno
    all_retorna_nodes = find_all_nodes(p.slice[5].value, list(), 'RETORNA')
    for index in range(len(all_retorna_nodes)):
        all_retorna_nodes[index] = all_retorna_nodes[index].anchestors[-1]

    retorna = list()
    for retorna_node in all_retorna_nodes:
        retorna_type = 'inteiro'
        if len(find_all_nodes(retorna_node, list(), 'NUM_PONTO_FLUTUANTE')) > 0:
            retorna_type = 'flutuante'
        elif len(find_all_nodes(retorna_node, list(), 'ID')) > 0:
            ids_call = find_all_nodes(retorna_node, list(), 'ID')

            for id_call in ids_call:
                label_id = id_call.children[0].label

                if label_id in func_list:
                    if label_id == name_func:
                        if type_func == 'flutuante':
                            retorna_type = 'flutuante'
                    else:
                        if func_list[label_id][0][1] == 'flutuante':
                            retorna_type = 'flutuante'
                elif label_id in var_list:
                    for index in range(len(var_list[label_id]) - 1, -1, -1):
                        if var_list[label_id][index][4] == name_func:
                            if var_list[label_id][index][1] == 'flutuante':
                                retorna_type = 'flutuante'
                            break
                        elif var_list[label_id][index][4] == 'global':
                            if var_list[label_id][index][1] == 'flutuante':
                                retorna_type = 'flutuante'
                            break
                else:
                    retorna_type = 'ERROR'

        retorna.append((retorna_type, retorna_node))

    if name_func in func_list:
        if func_list[name_func][0][-2]:
            message = ('ERROR', f'Erro: Função "{name_func}" já declarada anteriormente.')
            message_list.append(message)
        else:
            func_list[name_func][0] = [name_func, type_func, num_var, name_parameter, retorna, line_start, line_end, True, func_list[name_func][0][-1]]
    else:
        func_list[name_func] = [[name_func, type_func, num_var, name_parameter, retorna, line_start, line_end, True, []]]


def p_lista_parametros(p):
    """lista_parametros : lista_parametros VIRGULA parametro
                    | parametro
                    | vazio
    """

    pai = MyNode(name='lista_parametros', type='LISTA_PARAMETROS')
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        filho2 = MyNode(name='virgula', type='VIRGULA', parent=pai)
        filho_sym2 = MyNode(name=',', type='SIMBOLO', parent=filho2)
        p[2] = filho2
        p[3].parent = pai


def p_parametro(p):
    """parametro : tipo DOIS_PONTOS ID
                | parametro ABRE_COLCHETE FECHA_COLCHETE
    """
    global escopo

    pai = MyNode(name='parametro', type='PARAMETRO')
    p[0] = pai
    p[1].parent = pai

    if p[2] == ':':
        filho2 = MyNode(name='dois_pontos', type='DOIS_PONTOS', parent=pai)
        filho_sym2 = MyNode(name=':', type='SIMBOLO', parent=filho2)
        p[2] = filho2

        filho3 = MyNode(name='ID', type='ID', parent=pai)
        filho_id = MyNode(name=p[3], type='ID', parent=filho3)
    else:
        filho2 = MyNode(name='abre_colchete', type='ABRE_COLCHETE', parent=pai)
        filho_sym2 = MyNode(name='[', type='SIMBOLO', parent=filho2)
        p[2] = filho2

        filho3 = MyNode(name='fecha_colchete', type='FECHA_COLCHETE', parent=pai)
        filho_sym3 = MyNode(name=']', type='SIMBOLO', parent=filho3)
    p[3] = filho3

    name_var = p.slice[-1].value.children[0].label
    type_var = p.slice[1].value.children[0].children[0].label

    dimensions = []
    dimension_name = []

    if name_var in var_list:
        var_list[name_var].append(
            [name_var, type_var, len(dimensions), dimension_name, escopo, p.lineno(2), list()])
    else:
        var_list[name_var] = [[name_var, type_var, len(dimensions), dimension_name, escopo, p.lineno(2), list()]]


def p_parametro_error(p):
    """parametro : tipo error ID
                | error ID
                | parametro error FECHA_COLCHETE
                | parametro ABRE_COLCHETE error
    """
    global parser

    print("Erro na definicao do parâmetro. Tipo ou parâmetro.")

    if len(p) > 3:
        print(f"Erro:p[0]:{p[0]}, p[1]:{p[1]}, p[2]:{p[2]}, p[3]:{p[3]}")
    else:
        print(f"Erro:p[0]:{p[0]}, p[1]:{p[1]}, p[2]:{p[2]}")
    error_line = p.lineno(2)
    father = MyNode(name=f'ERROR::{error_line}', type='ERROR')
    logging.error(f"Syntax error parsing index rule at line {error_line}")
    parser.errok()
    p[0] = father


def p_corpo(p):
    """corpo : corpo acao
            | vazio
    """

    pai = MyNode(name='corpo', type='CORPO')
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai


def p_acao(p):
    """acao : expressao
        | declaracao_variaveis
        | se
        | repita
        | leia
        | escreva
        | retorna
    """
    pai = MyNode(name='acao', type='ACAO')
    p[0] = pai
    p[1].parent = pai


def p_se_error(p):
    """se : error expressao ENTAO corpo FIM
        | SE expressao error corpo FIM
        | error expressao ENTAO corpo SENAO corpo FIM
        | SE expressao error corpo SENAO corpo FIM
        | SE expressao ENTAO corpo error corpo FIM
        | SE expressao ENTAO corpo SENAO corpo
    """
    global parser

    print("Erro na definicao do SE. Expressão ou corpo.")

    if len(p) == 8:
        print(
            f"Erro:p[0]:{p[0]}, p[1]:{p[1]}, p[2]:{p[2]}, p[3]:{p[3]}, p[4]:{p[4]}, p[5]:{p[5]}, p[6]:{p[6]}, p[7]:{p[7]}")
    else:
        print(f"Erro:p[0]:{p[0]}, p[1]:{p[1]}, p[2]:{p[2]}, p[3]:{p[3]}, p[4]:{p[4]}, p[5]:{p[5]}")
    error_line = p.lineno(2)
    father = MyNode(name=f'ERROR::{error_line}', type='ERROR')
    logging.error(f"Syntax error parsing index rule at line {error_line}")
    parser.errok()
    p[0] = father


# Sub-árvore:
#       ________ (se) ________________________________
#      /    /          \      \         \      \      \
# (SE) (expressao)  (ENTAO)  (corpo) (SENAO) (corpo) (FIM)
#  |       |           |
# (se)   (...)      (então) ....

def p_se(p):
    """se : SE expressao ENTAO corpo FIM
        | SE expressao ENTAO corpo SENAO corpo FIM
    """

    pai = MyNode(name='se', type='SE')
    p[0] = pai

    filho1 = MyNode(name='SE', type='SE', parent=pai)
    filho_se = MyNode(name=p[1], type='SE', parent=filho1)
    p[1] = filho1

    p[2].parent = pai

    filho3 = MyNode(name='ENTAO', type='ENTAO', parent=pai)
    filho_entao = MyNode(name=p[3], type='ENTAO', parent=filho3)
    p[3] = filho3

    p[4].parent = pai

    if len(p) == 8:
        filho5 = MyNode(name='SENAO', type='SENAO', parent=pai)
        filho_senao = MyNode(name=p[5], type='SENAO', parent=filho5)
        p[5] = filho5

        p[6].parent = pai

        filho7 = MyNode(name='FIM', type='FIM', parent=pai)
        filho_fim = MyNode(name=p[7], type='FIM', parent=filho7)
        p[7] = filho7
    else:
        filho5 = MyNode(name='fim', type='FIM', parent=pai)
        filho_fim = MyNode(name=p[5], type='FIM', parent=filho5)
        p[5] = filho5


def p_repita(p):
    "repita : REPITA corpo ATE expressao"

    pai = MyNode(name='repita', type='REPITA')
    p[0] = pai

    filho1 = MyNode(name='REPITA', type='REPITA', parent=pai)
    filho_repita = MyNode(name=p[1], type='REPITA', parent=filho1)
    p[1] = filho1

    p[2].parent = pai  # corpo.

    filho3 = MyNode(name='ATE', type='ATE', parent=pai)
    filho_ate = MyNode(name=p[1], type='ATE', parent=filho3)
    p[3] = filho3

    p[4].parent = pai  # expressao.


def p_repita_error(p):
    """repita : error corpo ATE expressao
            | REPITA corpo error expressao
    """
    global parser

    print("Erro na definicao do REPITA. Expressão ou corpo.")

    print(f"Erro:p[0]:{p[0]}, p[1]:{p[1]}, p[2]:{p[2]}, p[3]:{p[3]}, p[4]:{p[4]}")
    error_line = p.lineno(2)
    father = MyNode(name=f'ERROR::{error_line}', type='ERROR')
    logging.error(f"Syntax error parsing index rule at line {error_line}")
    parser.errok()
    p[0] = father


def p_atribuicao(p):
    "atribuicao : var ATRIBUICAO expressao"

    pai = MyNode(name='atribuicao', type='ATRIBUICAO')
    p[0] = pai

    p[1].parent = pai

    filho2 = MyNode(name='ATRIBUICAO', type='ATRIBUICAO', parent=pai)
    filho_sym2 = MyNode(name=':=', type='SIMBOLO', parent=filho2)
    p[2] = filho2

    p[3].parent = pai

    get_call_var(p.slice[0].value, p.lineno(2))


def p_leia(p):
    "leia : LEIA ABRE_PARENTESE var FECHA_PARENTESE"

    pai = MyNode(name='leia', type='LEIA')
    p[0] = pai

    filho1 = MyNode(name='LEIA', type='LEIA', parent=pai)
    filho_sym1 = MyNode(name=p[1], type='LEIA', parent=filho1)
    p[1] = filho1

    filho2 = MyNode(name='abre_parentese', type='ABRE_PARENTESE', parent=pai)
    filho_sym2 = MyNode(name='(', type='SIMBOLO', parent=filho2)
    p[2] = filho2

    p[3].parent = pai  # var

    filho4 = MyNode(name='fecha_parentese', type='FECHA_PARENTESE', parent=pai)
    filho_sym4 = MyNode(name=')', type='SIMBOLO', parent=filho4)
    p[4] = filho4

    linha = p.lineno(2)
    get_call_var(p.slice[0].value, linha, False)


def p_leia_error(p):
    """leia : LEIA ABRE_PARENTESE error FECHA_PARENTESE
    """
    global parser

    print("Erro na definicao do LEIA. Variável.")

    print(f"Erro:p[0]:{p[0]}, p[1]:{p[1]}, p[2]:{p[2]}, p[3]:{p[3]}, p[4]:{p[4]}")
    error_line = p.lineno(2)
    father = MyNode(name=f'ERROR::{error_line}', type='ERROR')
    logging.error(f"Syntax error parsing index rule at line {error_line}")
    parser.errok()
    p[0] = father


def p_escreva(p):
    "escreva : ESCREVA ABRE_PARENTESE expressao FECHA_PARENTESE"

    pai = MyNode(name='escreva', type='ESCREVA')
    p[0] = pai

    filho1 = MyNode(name='ESCREVA', type='ESCREVA', parent=pai)
    filho_sym1 = MyNode(name=p[1], type='ESCREVA', parent=filho1)
    p[1] = filho1

    filho2 = MyNode(name='abre_parentese', type='ABRE_PARENTESE', parent=pai)
    filho_sym2 = MyNode(name='(', type='SIMBOLO', parent=filho2)
    p[2] = filho2

    p[3].parent = pai  # expressao.

    filho4 = MyNode(name='fecha_parentese', type='FECHA_PARENTESE', parent=pai)
    filho_sym4 = MyNode(name=')', type='SIMBOLO', parent=filho4)
    p[4] = filho4

    get_call_var(p.slice[0].value, p.lineno(2))


def p_retorna(p):
    "retorna : RETORNA ABRE_PARENTESE expressao FECHA_PARENTESE"

    pai = MyNode(name='retorna', type='RETORNA')
    p[0] = pai

    filho1 = MyNode(name='RETORNA', type='RETORNA', parent=pai)
    filho_sym1 = MyNode(name=p[1], type='RETORNA', parent=filho1)
    p[1] = filho1

    filho2 = MyNode(name='abre_parentese', type='ABRE_PARENTESE', parent=pai)
    filho_sym2 = MyNode(name='(', type='SIMBOLO', parent=filho2)
    p[2] = filho2

    p[3].parent = pai  # expressao.

    filho4 = MyNode(name='fecha_parentese', type='FECHA_PARENTESE', parent=pai)
    filho_sym4 = MyNode(name=')', type='SIMBOLO', parent=filho4)
    p[4] = filho4

    get_call_var(p.slice[0].value, p.lineno(2))


def p_expressao(p):
    """expressao : expressao_logica
                    | atribuicao
    """
    pai = MyNode(name='expressao', type='EXPRESSAO')
    p[0] = pai
    p[1].parent = pai


def p_expressao_logica(p):
    """expressao_logica : expressao_simples
                    | expressao_logica operador_logico expressao_simples
    """
    pai = MyNode(name='expressao_logica', type='EXPRESSAO_LOGICA')
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai
        p[3].parent = pai


def p_expressao_simples(p):
    """expressao_simples : expressao_aditiva
                        | expressao_simples operador_relacional expressao_aditiva
    """

    pai = MyNode(name='expressao_simples', type='EXPRESSAO_SIMPLES')
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai
        p[3].parent = pai


def p_expressao_aditiva(p):
    """expressao_aditiva : expressao_multiplicativa
                        | expressao_aditiva operador_soma expressao_multiplicativa
    """

    pai = MyNode(name='expressao_aditiva', type='EXPRESSAO_ADITIVA')
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai
        p[3].parent = pai


def p_expressao_multiplicativa(p):
    """expressao_multiplicativa : expressao_unaria
                            | expressao_multiplicativa operador_multiplicacao expressao_unaria
        """

    pai = MyNode(name='expressao_multiplicativa', type='EXPRESSAO_MULTIPLICATIVA')
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai
        p[3].parent = pai


def p_expressao_unaria(p):
    """expressao_unaria : fator
                        | operador_soma fator
                        | operador_negacao fator
        """
    pai = MyNode(name='expressao_unaria', type='EXPRESSAO_UNARIA')
    p[0] = pai
    p[1].parent = pai

    if p[1] == '!':
        filho1 = MyNode(name='operador_negacao', type='OPERADOR_NEGACAO', parent=pai)
        filho_sym1 = MyNode(name=p[1], type='SIMBOLO', parent=filho1)
        p[1] = filho1
    else:
        p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai


def p_operador_relacional(p):
    """operador_relacional : MENOR
                            | MAIOR
                            | IGUAL
                            | DIFERENTE 
                            | MENOR_IGUAL
                            | MAIOR_IGUAL
    """
    pai = MyNode(name='operador_soma', type='OPERADOR_SOMA')
    p[0] = pai

    if p[1] == "<":
        filho = MyNode(name='menor', type='MENOR', parent=pai)
        filho_sym = MyNode(name=p[1], type='SIMBOLO', parent=filho)
    elif p[1] == ">":
        filho = MyNode(name='maior', type='MAIOR', parent=pai)
        filho_sym = MyNode(name=p[1], type='SIMBOLO', parent=filho)
    elif p[1] == "=":
        filho = MyNode(name='igual', type='IGUAL', parent=pai)
        filho_sym = MyNode(name=p[1], type='SIMBOLO', parent=filho)
    elif p[1] == "<>":
        filho = MyNode(name='diferente', type='DIFERENTE', parent=pai)
        filho_sym = MyNode(name=p[1], type='SIMBOLO', parent=filho)
    elif p[1] == "<=":
        filho = MyNode(name='menor_igual', type='MENOR_IGUAL', parent=pai)
        filho_sym = MyNode(name=p[1], type='SIMBOLO', parent=filho)
    elif p[1] == ">=":
        filho = MyNode(name='maior_igual', type='MAIOR_IGUAL', parent=pai)
        filho_sym = MyNode(name=p[1], type='SIMBOLO', parent=filho)
    else:
        print('Erro operador relacional')

    # p[1] = filho


def p_operador_soma(p):
    """operador_soma : MAIS
                    | MENOS
    """
    if p[1] == "+":
        mais = MyNode(name='mais', type='MAIS')
        mais_lexema = MyNode(name='+', type='SIMBOLO', parent=mais)
        p[0] = MyNode(name='operador_soma', type='OPERADOR_SOMA', children=[mais])
    else:
        menos = MyNode(name='menos', type='MENOS')
        menos_lexema = MyNode(name='-', type='SIMBOLO', parent=menos)
        p[0] = MyNode(name='operador_soma', type='OPERADOR_SOMA', children=[menos])


def p_operador_logico(p):
    """operador_logico : E
                    | OU
    """
    if p[1] == "&&":
        filho = MyNode(name='e', type='E')
        filho_lexema = MyNode(name=p[1], type='SIMBOLO', parent=filho)
        p[0] = MyNode(name='operador_logico', type='OPERADOR_LOGICO', children=[filho])
    else:
        filho = MyNode(name='ou', type='OU')
        filho_lexema = MyNode(name=p[1], type='SIMBOLO', parent=filho)
        p[0] = MyNode(name='operador_logico', type='OPERADOR_SOMA', children=[filho])


def p_operador_negacao(p):
    "operador_negacao : NAO"

    if p[1] == "!":
        filho = MyNode(name='nao', type='NAO')
        negacao_lexema = MyNode(name=p[1], type='SIMBOLO', parent=filho)
        p[0] = MyNode(name='operador_negacao', type='OPERADOR_NEGACAO', children=[filho])


def p_operador_multiplicacao(p):
    """operador_multiplicacao : VEZES
                            | DIVIDE
        """
    if p[1] == "*":
        filho = MyNode(name='vezes', type='VEZES')
        vezes_lexema = MyNode(name=p[1], type='SIMBOLO', parent=filho)
        p[0] = MyNode(name='operador_multiplicacao', type='OPERADOR_MULTIPLICACAO', children=[filho])
    else:
        divide = MyNode(name='divide', type='DIVIDE')
        divide_lexema = MyNode(name=p[1], type='SIMBOLO', parent=divide)
        p[0] = MyNode(name='operador_soma', type='OPERADOR_SOMA', children=[divide])


def p_fator(p):
    """fator : ABRE_PARENTESE expressao FECHA_PARENTESE
            | var
            | chamada_funcao
            | numero
        """
    pai = MyNode(name='fator', type='FATOR')
    p[0] = pai
    if len(p) > 2:
        filho1 = MyNode(name='abre_parentese', type='ABRE_PARENTESE', parent=pai)
        filho_sym1 = MyNode(name=p[1], type='SIMBOLO', parent=filho1)
        p[1] = filho1

        p[2].parent = pai

        filho3 = MyNode(name='fecha_parentese', type='FECHA_PARENTESE', parent=pai)
        filho_sym3 = MyNode(name=p[3], type='SIMBOLO', parent=filho3)
        p[3] = filho3
    else:
        p[1].parent = pai


def p_fator_error(p):
    """fator : ABRE_PARENTESE error FECHA_PARENTESE
    """
    global parser

    print("Erro na definicao do Fator. Expressão ou variável.")

    if len(p) > 2:
        print(f"Erro:p[0]:{p[0]}, p[1]:{p[1]}, p[2]:{p[2]}, p[3]:{p[3]}")
    else:
        print(f"Erro:p[0]:{p[0]}, p[1]:{p[1]}")
    error_line = p.lineno(2)
    father = MyNode(name=f'ERROR::{error_line}', type='ERROR')
    logging.error(f"Syntax error parsing index rule at line {error_line}")
    parser.errok()
    p[0] = father


def p_numero(p):
    """numero : NUM_INTEIRO
                | NUM_PONTO_FLUTUANTE
                | NUM_NOTACAO_CIENTIFICA
    """

    pai = MyNode(name='numero', type='NUMERO')
    p[0] = pai

    if str(p[1]).find('.') == -1:
        aux = MyNode(name='NUM_INTEIRO', type='NUM_INTEIRO', parent=pai)
        aux_val = MyNode(name=p[1], type='VALOR', parent=aux)
        p[1] = aux
    elif str(p[1]).find('e') >= 0:
        aux = MyNode(name='NUM_NOTACAO_CIENTIFICA', type='NUM_NOTACAO_CIENTIFICA', parent=pai)
        aux_val = MyNode(name=p[1], type='VALOR', parent=aux)
        p[1] = aux
    else:
        aux = MyNode(name='NUM_PONTO_FLUTUANTE', type='NUM_PONTO_FLUTUANTE', parent=pai)
        aux_val = MyNode(name=p[1], type='VALOR', parent=aux)
        p[1] = aux


def p_chamada_funcao(p):
    "chamada_funcao : ID ABRE_PARENTESE lista_argumentos FECHA_PARENTESE"

    pai = MyNode(name='chamada_funcao', type='CHAMADA_FUNCAO')
    p[0] = pai
    if len(p) > 2:
        filho1 = MyNode(name='ID', type='ID', parent=pai)
        filho_id = MyNode(name=p[1], type='ID', parent=filho1)
        p[1] = filho1

        filho2 = MyNode(name='abre_parentese', type='ABRE_PARENTESE', parent=pai)
        filho_sym = MyNode(name=p[2], type='SIMBOLO', parent=filho2)
        p[2] = filho2

        p[3].parent = pai

        filho4 = MyNode(name='fecha_parentese', type='FECHA_PARENTESE', parent=pai)
        filho_sym = MyNode(name=p[4], type='SIMBOLO', parent=filho4)
        p[4] = filho4
    else:
        p[1].parent = pai

    get_call_var(p.slice[3].value, p.lineno(2))
    get_call_func(p.slice[0].value, p.lineno(2), p)


def p_lista_argumentos(p):
    """lista_argumentos : lista_argumentos VIRGULA expressao
                    | expressao
                    | vazio
        """
    pai = MyNode(name='lista_argumentos', type='LISTA_ARGUMENTOS')
    p[0] = pai

    if len(p) > 2:
        p[1].parent = pai

        filho2 = MyNode(name='VIRGULA', type='VIRGULA', parent=pai)
        filho_sym = MyNode(name=p[2], type='SIMBOLO', parent=filho2)
        p[2] = filho2

        p[3].parent = pai
    else:
        p[1].parent = pai


def p_vazio(p):
    "vazio : "

    pai = MyNode(name='vazio', type='VAZIO')
    p[0] = pai

def p_declaracao_funcao_error(p):
    """declaracao_funcao :  error 
    """
    print("Erro ao definir a função")
    error_line = p.lineno(2)
    father = MyNode(name='ERROR::{}'.format(error_line), type='ERROR')
    logging.error(
        "Erro ao definir a função na linha{}".format(error_line))
    parser.errok()
    p[0] = father


def p_error(p):
    if p:
        token = p
        print("Erro:[{line},{column}]: Erro próximo ao token '{token}'".format(line=token.lineno, column=token.lineno,
                                                                               token=token.value))


# Build the sintatic.
def main():
    global root, parser, tokens
    root = None
    # argv[1] = 'teste.tpp'
    aux = argv[1].split('.')
    if aux[-1] != 'tpp':
      raise IOError("Not a .tpp file!")
    data = open(argv[1])

    source_file = data.read()
    parser.parse(source_file)

    if root and root.children != ():
        print("Generating Syntax Tree Graph...")
        DotExporter(root).to_picture(argv[1] + ".ast.png")
        UniqueDotExporter(root).to_picture(argv[1] + ".unique.ast.png")
        DotExporter(root).to_dotfile(argv[1] + ".ast.dot")
        UniqueDotExporter(root).to_dotfile(argv[1] + ".unique.ast.dot")
        print(RenderTree(root, style=AsciiStyle()).by_attr())
        print("Graph was generated.\nOutput file: " + argv[1] + ".ast.png")

        DotExporter(root, graph="graph",
                    nodenamefunc=MyNode.nodenamefunc,
                    nodeattrfunc=lambda node: 'label=%s' % (node.type),
                    edgeattrfunc=MyNode.edgeattrfunc,
                    edgetypefunc=MyNode.edgetypefunc).to_picture(argv[1] + ".ast2.png")

        # DotExporter(root, nodenamefunc=lambda node: node.label).to_picture(argv[1] + ".ast3.png")
    else:
        print("Unable to generate Syntax Tree.")
    print('\n\n')

    print('\n\n')

    return root, func_list, var_list, message_list


# Build the parser.
    # parser = yacc.yacc(optimize=True, start='programa', debug=True, debuglog=log)
parser = yacc.yacc(method="LALR", optimize=True, start='programa', debug=True, debuglog=log, write_tables=False,
                    tabmodule='tpp_parser_tab')

if __name__ == "__main__":
    main()