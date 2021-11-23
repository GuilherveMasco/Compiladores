import ply.lex as lex
import logging

from ply.lex import TOKEN

logging.basicConfig(
     level = logging.DEBUG,
     filename = "lex.log",
     filemode = "w",
     format = "%(filename)10s:%(lineno)4d:%(message)s"
)
log = logging.getLogger()

class tppLex():

    # Variáveis
    digito = r"([0-9])"
    letra = r"([a-zA-ZáÁãÃàÀéÉíÍóÓõÕ])"
    sinal = r"([\-\+]?)"
    
    # Tokens e simblos da linguagens
    tokens = [
        "ID",  # identificador
        # numerais
        "NUM_NOTACAO_CIENTIFICA",  # ponto flutuante em notaçao científica
        "NUM_PONTO_FLUTUANTE",  # ponto flutuate
        "NUM_INTEIRO",  # inteiro

        # operadores binarios
        "MAIS",  # +
        "MENOS",  # -
        "VEZES",  # *
        "DIVIDE",  # /
        "E",  # &&
        "OU",  # ||
        "DIFERENTE",  # <>
        "MENOR_IGUAL",  # <=
        "MAIOR_IGUAL",  # >=
        "MENOR",  # <
        "MAIOR",  # >
        "IGUAL",  # =

        # operadores unarios
        "NAO",  # !

        # simbolos
        "ABRE_PARENTESE",  # (
        "FECHA_PARENTESE",  # )
        "ABRE_COLCHETE",  # [
        "FECHA_COLCHETE",  # ]
        "VIRGULA",  # ,
        "DOIS_PONTOS",  # :
        "ATRIBUICAO",  # :=
        # 'COMENTARIO', # {***}
    ]

    # Plavras reservadas da linguagens
    reserved_words = {
        "se": "SE",
        "então": "ENTAO",
        "senão": "SENAO",
        "fim": "FIM",
        "repita": "REPITA",
        "flutuante": "FLUTUANTE",
        "retorna": "RETORNA",
        "até": "ATE",
        "leia": "LEIA",
        "escreva": "ESCREVA",
        "inteiro": "INTEIRO",
    }

    tokens = tokens + list(reserved_words.values())

    # Expressões Regulares para tokens simples:
    # Símbolos.
    t_MAIS = r'\+'
    t_MENOS = r'-'
    t_VEZES = r'\*'
    t_DIVIDE = r'/'
    t_ABRE_PARENTESE = r'\('
    t_FECHA_PARENTESE = r'\)'
    t_ABRE_COLCHETE = r'\['
    t_FECHA_COLCHETE = r'\]'
    t_VIRGULA = r','
    t_ATRIBUICAO = r':='
    t_DOIS_PONTOS = r':'

    # Operadores Lógicos.
    t_E = r'&&'
    t_OU = r'\|\|'
    t_NAO = r'!'

    # Operadores Relacionais.
    t_DIFERENTE = r'<>'
    t_MENOR_IGUAL = r'<='
    t_MAIOR_IGUAL = r'>='
    t_MENOR = r'<'
    t_MAIOR = r'>'
    t_IGUAL = r'='
    
    # Outras Expressões Regulares
    id = (
        r"(" + letra + r"(" + digito + r"+|_|" + letra + r")*)"
    )  # o mesmo que '((letra)(letra|_|([0-9]))*)'

    def t_COMENTARIO(self,token):
        r"(\{((.|\n)*?)\})"
        token.lexer.lineno += token.value.count("\n")

    @TOKEN(id)
    def t_ID(self,token):
        token.type = self.reserved_words.get(
            token.value, "ID"
        )  # não é necessário fazer regras/regex para cada palavra reservada
        # se o token não for uma palavra reservada automaticamente é um id
        # As palavras reservadas têm precedências sobre os ids

        return token

    def t_NUM_NOTACAO_CIENTIFICA(self,token):
        r"([\d][\.]?[\d]*[eE][+-]?[\d]+)"
        return token

    def t_NUM_PONTO_FLUTUANTE(self,token):
        r"[\d]+\.[\d]*"
        return token

    def t_NUM_INTEIRO(self,token):
        r"[\d]+"
        return token

    # Regra para contar o número de linhas 
    def t_newline(self,token):
        r'\n+'
        token.lexer.lineno += len(token.value)

    # Ignorar os espaços e tabs
    t_ignore  = ' \t'

    # Tratamento de erro
    def t_error(self,token):
        print("Caracter inválido '%s'" % token.value[0])
        token.lexer.skip(1) # segue o código quando encontra caracter ilegal

    # Build the lexer.
    def build(self,**kwargs):
        return lex.lex(module=self, **kwargs)