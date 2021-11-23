import sys
import numpy as np

from tabulate import tabulate
from anytree import Node, RenderTree
from anytree.exporter import UniqueDotExporter

import tppparser


def find_all_nodes(root, label, list_node):
    for node in root.children:
        list_node = find_all_nodes(node, label, list_node)
        if node.label == label:
            list_node.append(node)

    return list_node


def find_all_father_nodes(sun, label, list_node):
    for index in range(len(sun.anchestors)-1, -1, -1):
        if sun.anchestors[index].label == label:
            list_node.append(sun.anchestors[index])

    return list_node


def find_all_parameters_sent(root, escope, list_node):

    for node in root.children:
        if node.label == 'chamada_funcao':
            func_name = node.descendants[1].label
            type_func = func_list[func_name][0][1]
            list_node.append((func_name, type_func))
            return list_node
        elif node.label == 'ID':
            var_name = node.children[0].label
            type_var = ''
            if var_name in var_list:
                for var in var_list[var_name]:
                    if var[4] == escope:
                        type_var = var[1]
                        break

                if type_var == '':
                    for var in var_list[var_name]:
                        if var[4] == 'global':
                            type_var = var[1]
                            break

                list_node.append((var_name, type_var))
                return list_node
        elif node.label == 'numero':
            type_num = node.children[0].label

            if type_num == 'NUM_INTEIRO':
                num = int(node.descendants[1].label)
                type_num = 'inteiro'
            else:
                type_num = 'flutuante'
                num = float(node.descendants[1].label)

            list_node.append((num, type_num))
            return list_node

        list_node = find_all_parameters_sent(node, escope, list_node)

    return list_node


def get_func_called(line, func_list):
    for element in func_list:
        for func in func_list[element]:
            if func[5] <= line < func[6]:
                return func[0]


def clean_tuple(lst):
    return [t for t in (set(tuple(i) for i in lst))]


def get_var_in_scope(element, escopo='global'):
    for var in var_list[element]:
        if var[4] == escopo:
            return var


def generate_table_func(list, header, list_index):
    table = [header]

    for element in list:
        for func in list[element]:
            aux_array = []
            for index in list_index:
                aux_array.append(func[index])
            table.append(aux_array)

    return table


def generate_table_var(list, header, list_index):
    table = [header]

    for element in list:
        for func in list[element]:
            aux_array = []
            for index in list_index:
                if index == 3:
                    dim_tam = []
                    for j in range(len(func[index])):
                        if func[index][j][1] == 'NUM_PONTO_FLUTUANTE':
                            value = float(func[index][j][0])
                        else:
                            value = int(func[index][j][0])
                        dim_tam.append(value)
                    aux_array.append(dim_tam)
                else:
                    aux_array.append(func[index])
            table.append(aux_array)

    return table


def check_principal(func_list, message_list):
    if 'principal' not in func_list or not func_list['principal'][0][7]:
        message = (
            'ERROR', f'Erro: Função principal não declarada.')
        message_list.append(message)
    else:
        line_start = func_list['principal'][0][5]
        line_end = func_list['principal'][0][6]

        for call in func_list['principal'][0][-1]:
            if not line_start <= call[0] < line_end:
                message = (
                    'ERROR', f'Erro: Chamada para a função principal não permitida.')
                message_list.append(message)


def check_return_of_all_functions(func_list, message_list):
    message = ''
    for element in func_list:
        for func in func_list[element]:
            type_func = func[1]

            return_types = list()
            for type_return in func[4]:
                return_types.append(type_return[0])

            return_types = list(set(return_types))

            if type_func == 'vazio':
                if len(return_types) > 0:
                    if len(return_types) > 1:
                        message = ('ERROR',
                                   f'Erro: Função {element} deveria retornar vazio, mas retorna {return_types[0]} e {return_types[1]}.')
                    else:
                        message = ('ERROR',
                                   f'Erro: Função {element} deveria retornar vazio, mas retorna {return_types[0]}.')
            elif type_func == 'inteiro':
                if len(return_types) == 0:
                    message = ('ERROR',
                               f'Erro: Função {element} deveria retornar inteiro, mas retorna vazio.')
                else:
                    for type_return in return_types:
                        if type_return != 'inteiro' and type_return != 'ERROR':
                            message = ('ERROR',
                                       f'Erro: Função {element} deveria retornar inteiro, mas retorna flutuante.')
                            break
            elif type_func == 'flutuante':
                if len(return_types) == 0:
                    message = ('ERROR',
                               f'Erro: Função {element} deveria retornar flutuante, mas retorna vazio.')
                else:
                    for type_return in return_types:
                        if type_return != 'flutuante' and type_return != 'ERROR':
                            message = ('ERROR',
                                       f'Erro: Função {element} deveria retornar flutuante, mas retorna inteiro.')
                            break

            if message != '':
                message_list.append(message)


def check_call_of_all_functions(func_list, message_list):
    message = ''
    for element in func_list:
        for func in func_list[element]:
            if not func[-2]:
                message = ('ERROR',
                           f'Erro: Chamada a função {element} que não foi declarada.')
                message_list.append(message)

            else:
                if len(func[-1]) == 0 and element != 'principal':
                    message = ('WARNING',
                               f'Aviso: Função {element} declarada, mas não utilizada.')
                    message_list.append(message)
                else:
                    calls = 0
                    recursion = 0
                    for call_func in func[-1]:
                        func_called = get_func_called(call_func[0], func_list)
                        if func_called != element:
                            calls += 1
                        else:
                            recursion += 1

                    if element == 'principal':
                        calls += 1

                    if calls == 0:
                        message = ('WARNING',
                                   f'Aviso: Função {element} declarada, mas não utilizada.')
                        message_list.append(message)

                    elif recursion > 0:
                        message = ('WARNING',
                                   f'Aviso: Chamada recursiva para {element}.')
                        message_list.append(message)

                for call in func[-1]:
                    list_parameters = find_all_parameters_sent(call[1].children[2], func[0], list())

                    if len(list_parameters) > func[2]:
                        message = ('ERROR',
                                   f'Erro: Chamada à função {func[0]} com número de parâmetros maior que o declarado.')
                        message_list.append(message)
                    elif len(list_parameters) < func[2]:
                        message = ('ERROR',
                                   f'Erro: Chamada à função {func[0]} com número de parâmetros menor que o declarado.')
                        message_list.append(message)
                    else:
                        parameters = []
                        for func in func_list[call[1].descendants[1].label]:
                            for var_func in func[3]:
                                for index in range(len(var_list[var_func])):
                                    if var_list[var_func][index][4] == call[1].descendants[1].label:
                                        parameters.append((var_list[var_func][index][0], var_list[var_func][index][1]))
                                        break

                        for index in range(len(parameters)):
                            type_index = list_parameters[index][1]
                            if type_index == 'NUM_PONTO_FLUTUANTE':
                                type_index = 'flutuante'
                            else:
                                type_index = 'inteiro'
                            if parameters[index][1] != type_index:
                                message = ('WARNING',
                                           f'Aviso: Coerção implícita do valor passado para váriavel ' +
                                           f'‘{parameters[index][0]}‘ da função ‘{call[1].descendants[1].label}’.')
                                message_list.append(message)


def check_call_of_all_variables(var_list, message_list, root):
    all_leia_node = find_all_nodes(root, 'LEIA', list())

    for index in range(len(all_leia_node)):
        all_leia_node[index] = all_leia_node[index].anchestors[-1]
        escope_read = find_all_father_nodes(all_leia_node[index], 'cabecalho', list())[0].descendants[1].label
        id_read = find_all_nodes(all_leia_node[index], 'ID', list())[0].children[0].label

        for var in var_list[id_read]:
            found = False
            if var[4] == escope_read:
                found = True
                if len(var[-1]) == 0:
                    message = ('WARNING',
                               f'Aviso: Variável ‘{id_read}’ declarada e não inicializada. ')
                    message_list.append(message)

            if not found:
                for var in var_list[id_read]:
                    if var[4] == 'global':
                        if len(var[-1]) == 0:
                            message = ('WARNING',
                                       f'Aviso: Variável ‘{id_read}’ declarada e não inicializada. ')
                            message_list.append(message)

    for element in var_list:
        for var in var_list[element]:
            if len(var[-1]) == 0:
                message = ('WARNING',
                           f'Aviso: Variável ‘{var[0]}’ declarada e não inicializada. ')
                message_list.append(message)

            if len(var_list[element]) > 1:
                for var2 in var_list[element]:
                    if var2 != var and var2[4] == var[4]:
                        message = ('WARNING', f'Aviso: Variável ‘{var2[0]}‘ já declarada anteriormente.')
                        message_list.append(message)


def check_all_atribuicao_type(var_list, message_list, root):
    all_atribuicao_node = find_all_nodes(root, 'atribuicao', list())

    for index in range(len(all_atribuicao_node)):
        try:
            escope_read = find_all_father_nodes(all_atribuicao_node[index], 'cabecalho', list())[0].descendants[1].label
        except:
            escope_read = 'global'

        # id_left = all_atribuicao_node[index].descendants[2].label
        right_side = find_all_parameters_sent(all_atribuicao_node[index], escope_read, list())
        left_side = right_side.pop(0)

        diferent_expression_type = False
        for unique_right in right_side:
            if unique_right[1] != left_side[1] and unique_right[1] != '':

                diferent_expression_type = unique_right[1]
                message = ('WARNING',
                           f'Aviso: Coerção implícita do valor de ‘{unique_right[0]}’.')
                message_list.append(message)

        if diferent_expression_type and diferent_expression_type != left_side[1]:
            message = ('WARNING',
                       f'Aviso: Atribuição de tipos distintos ‘{left_side[0]}’ {left_side[1]} e ‘expressão’ {diferent_expression_type}')
            message_list.append(message)


def check_all_var_array(var_list, message_list):
    for element in var_list:
        for var in var_list[element]:
            if var[2] != 0:
                for dimension in var[3]:
                    dimension_number = 0
                    if dimension[1] != 'NUM_INTEIRO':
                        dimension_number = float(dimension[0])
                        message = ('ERROR',
                                   f'Erro: Índice de array ‘{var[0]}’ não inteiro.')
                        message_list.append(message)
                    else:
                        dimension_number = int(dimension[0])
                for call in var[-1]:
                    numero = find_all_nodes(call[1].descendants[3], 'numero', list())
                    if len(numero) > 0:
                        if len(find_all_nodes(numero[0], 'NUM_PONTO_FLUTUANTE', list())) > 0:
                            message = ('ERROR',
                                       f'Erro: Índice de array ‘{var[0]}’ não inteiro.')
                            message_list.append(message)
                        else:
                            numero = int(numero[0].descendants[-1].label)
                            if numero > dimension_number - 1:
                                message = ('ERROR',
                                           f'Erro: Índice de array ‘{var[0]}’ fora do intervalo (out of range).')
                                message_list.append(message)


def do_all_semantic_check(func_list, var_list, message_list, func_table, var_table, root):
    check_principal(func_list, message_list)
    check_return_of_all_functions(func_list, message_list)
    check_call_of_all_functions(func_list, message_list)
    check_call_of_all_variables(var_list, message_list, root)
    check_all_atribuicao_type(var_list, message_list, root)
    check_all_var_array(var_list, message_list)


def poda_arvore(root, labels):
    for node in root.children:
        poda_arvore(node, labels)

    if root.label in labels:
        dad = root.parent
        aux = []
        for children in dad.children:
            if children != root:
                aux.append(children)
        for children in root.children:
            aux.append(children)
        root.children = aux
        dad.children = aux

    if root.label == 'declaracao_funcao':
        corpo = root.children[1]
        aux = []
        for children in root.children:
            if children.label == 'fim':
                aux.append(corpo)
            if children != corpo:
                aux.append(children)
        root.children = aux

    if root.label == 'corpo' and len(root.children) == 0:
        dad = root.parent
        aux = []
        for children in dad.children:
            if children != root:
                aux.append(children)
        for children in root.children:
            aux.append(children)
        root.children = aux
        dad.children = aux

def ajusta_arvore(root, labels_ajuste):
    for node in root.children:
        ajusta_arvore(node, labels_ajuste)

    dad = root.parent
    aux = []

    if root.label == 'repita' and len(root.children) > 0:
        for children in root.children:
            if children.label != 'repita':
                aux.append(children)
        root.children = aux
        aux = []

    if root.label == 'e' and root.children[0].label == '&&':
        root.children = []
        root.label = '&&'
        root.name = '&&'

    if root.label == 'ou' and root.children[0].label == '||':
        root.children = []
        root.label = '||'
        root.name = '||'


    if root.label == 'se' and len(root.children) > 0:
        for children in root.children:
            if children.label != 'se':
                aux.append(children)

        root.children = aux
        aux = []

    if root.label == 'ATE':
        root.children = []
        root.label = 'até'
        root.name = 'até'

    if root.label == 'leia' or root.label == 'escreva' or root.label == 'retorna':
        if len(root.children) == 0:
            for children in dad.children:
                if children != root:
                    aux.append(children)

            dad.children = aux

    # if root.label in labels_ajuste:
    #     if root.label == ':=':
    #         for children in dad.children:
    #             if children != root:
    #                 aux.append(children)
    #
    #         root.children = aux
    #         dad.children = [root]
    #     else:
    #         dad_aux = []
    #         for index in range(len(dad.children)):
    #             if dad.children[index] == root:
    #                 aux.append(dad.children[index - 1])
    #                 if len(dad.children) > 1:
    #                     aux.append(dad.children[index + 1])
    #
    #                 for j in range(len(dad.children)):
    #                     if j != index or j != index - 1 or j != index + 1:
    #                         dad_aux.append(dad.children[j])
    #                     if j == index:
    #                         dad_aux.append(root)
    #
    #         if len(dad.children) > 1:
    #             root.children = aux


def main():
    global root, func_list, var_list, message_list

    root, func_list, var_list, message_list = tppparser.main()

    # Checar se as chamadas estão no escopo correto caso contrario trocar os escopos
    for element in var_list:
        for index_var in range(len(var_list[element])):
            escopo_atual = var_list[element][index_var][4]
            if escopo_atual != 'global':
                len_call_list = len(var_list[element][index_var][-1])
                tuple_call_index = 0

                while tuple_call_index < len_call_list:
                    tuple_call = var_list[element][index_var][-1][tuple_call_index]
                    if func_list[escopo_atual][0][5] <= tuple_call[0] < func_list[escopo_atual][0][6]:
                        pass
                    else:
                        new_var_escopo = get_var_in_scope(element, 'global')
                        new_var_escopo[-1].append(tuple_call)
                        var_list[element][index_var][-1].pop(tuple_call_index)
                        len_call_list -= 1
                        tuple_call_index -= 1

                    tuple_call_index += 1

    # # Remover tuplas iguais das chamadas de variaveis
    # for element in var_list:
    #     for index_var in range(len(var_list[element])):
    #         var_list[element][index_var][-1] = clean_tuple(var_list[element][index_var][-1])

    func_table = generate_table_func(func_list, ['Lexema', 'Tipo', 'Num. Parâmetros', 'Parâmetros', 'Init',
                                                 'Linha Inicial', 'Linha Final'], [0, 1, 2, 3, 7, 5, 6])

    var_table = generate_table_var(var_list, ['Lexema', 'Tipo', 'Dimensões', 'Tamanho Dimensões', 'Escopo', 'Linha'],
                                   [0, 1, 2, 3, 4, 5])

    print(f'TABELA DE FUNÇÕES:\n{tabulate(func_table, headers="firstrow", tablefmt="fancy_grid")}')
    print('\n\n')
    print(f'TABELA DE VARIÁVEIS:\n{tabulate(var_table, headers="firstrow", tablefmt="fancy_grid")}')
    print('\n\n')

    do_all_semantic_check(func_list, var_list, message_list, func_table, var_table, root)

    erros = 0
    message_list = clean_tuple(message_list)
    for message in message_list:
        print(message[-1])
        if message[0] == 'ERROR':
            erros += 1


    print('\n\n')
    # if erros == 0:
    label_remove_nodes = ['ID', 'var', 'lista_variaveis', 'dois_pontos', 'tipo',
                        'INTEIRO', 'FLUTUANTE', 'NUM_INTEIRO', 'NUM_PONTO_FLUTUANTE',
                        'NUM_NOTACAO_CIENTIFICA', 'LEIA', 'abre_parentese', 'fecha_parentese',
                        'lista_declaracoes', 'declaracao', 'indice', 'numero', 'fator',
                        'abre_colchete', 'fecha_colchete', 'expressao', 'expressao_logica',
                        'expressao_simples', 'expressao_aditiva', 'expressao_multiplicativa',
                        'expressao_unaria', 'inicializacao_variaveis', 'ATRIBUICAO', 'atribuicao',
                        'operador_soma', 'mais', 'chamada_funcao', 'lista_argumentos', 'VIRGULA',
                        'virgula', 'fator', 'cabecalho', 'FIM', 'lista_parametros', 'vazio',
                        '(', ')', ':', ',', 'RETORNA', 'ESCREVA', 'SE', 'ENTAO', 'SENAO', 'maior',
                        'menor', 'REPITA', 'igual', 'menos', 'menor_igual', 'maior_igual', 'operador_logico',
                        'operador_multiplicacao', 'vezes']
    labels_ajuste = [':=', '+', '*', '-', '/']
    poda_arvore(root, label_remove_nodes)
    ajusta_arvore(root, labels_ajuste)
    UniqueDotExporter(root).to_picture(f"{sys.argv[1]}.cut.unique.ast.png")
    print(f"Poda da árvore gerada\nArquivo de destino: {sys.argv[1]}.cut.unique.ast.png")
    # else:
    #     print(f"Não foi possível gerar a árvore abstrata, devido a erros semânticos")

    return root, message_list, func_list, var_list


if __name__ == '__main__':
    main()