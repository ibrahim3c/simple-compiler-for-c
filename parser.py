"""
Program      -> DeclarationList
DeclarationList -> Declaration DeclarationList | ε
Declaration  -> Type Identifier ';' | Type Identifier '=' Expression ';' | Function
Function     -> Type Identifier '(' ')' '{' DeclarationList '}'
Type         -> 'int' | 'float' | 'double' | 'char'
Expression   -> Number | Identifier
Identifier   -> IDENTIFIER
Number       -> NUMBER

"""

from lexer import Lexer
class ParseNode:
    def __init__(self, name, children=None):
        self.name = name
        self.children = children or []

    def __repr__(self, level=0):
        ret = "  " * level + self.name + "\n"
        for child in self.children:
            ret += child.__repr__(level + 1)
        return ret

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0

    def current_token(self):
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def consume(self, expected_type=None, expected_value=None):
        token = self.current_token()
        if token is None:
            raise Exception("Unexpected end of input")
        if expected_type and token.token_type != expected_type:
            raise Exception(f"Expected {expected_type}, got {token.token_type}")
        if expected_value and token.value != expected_value:
            raise Exception(f"Expected '{expected_value}', got '{token.value}'")
        self.index += 1
        return token

    def parse_program(self):
        children = []
        while self.index < len(self.tokens):
            children.append(self.parse_declaration())
        return ParseNode("Program", children)

    def parse_declaration(self):
        # Declaration -> Type Identifier ';'
        #              | Type Identifier '=' Expression ';'
        #              | Function
        #              | Expression ';'
        if self.current_token().token_type == "KEYWORD":  # Start with a type
            type_node = self.parse_type()
            id_token = self.consume("IDENTIFIER")
            id_node = ParseNode(f"Identifier({id_token.value})")

            if self.current_token() and self.current_token().value == '(':
                return self.parse_function(type_node, id_node)

            if self.current_token() and self.current_token().value == '=':
                self.consume("OPERATOR")  # Consume '='
                expr_node = self.parse_expression()
                self.consume("DELIMITER")  # Consume ';'
                return ParseNode("VariableDeclaration", [type_node, id_node, expr_node])

            self.consume("DELIMITER")  # Consume ';'
            return ParseNode("VariableDeclaration", [type_node, id_node])

        else:  # It might be an expression (like a function call)
            expr_node = self.parse_expression()
            self.consume("DELIMITER")  # Consume ';'
            return ParseNode("ExpressionStatement", [expr_node])

    def parse_function(self, type_node, id_node):
        # Function -> Type Identifier '(' ')' '{' DeclarationList '}'
        self.consume("DELIMITER", "(")  # Consume '('
        self.consume("DELIMITER", ")")  # Consume ')'
        self.consume("DELIMITER", "{")  # Consume '{'
        body_node = self.parse_declaration_list()
        self.consume("DELIMITER", "}")  # Consume '}'
        return ParseNode("Function", [type_node, id_node, body_node])

    def parse_declaration_list(self):
        # DeclarationList -> Declaration DeclarationList | ε
        children = []
        while self.current_token() and self.current_token().value != '}':
            children.append(self.parse_declaration())
        return ParseNode("DeclarationList", children)

    def parse_type(self):
        # Type -> 'int' | 'float' | 'double' | 'char'
        token = self.consume("KEYWORD")
        if token.value not in {"int", "float", "double", "char"}:
            raise Exception(f"Unexpected type {token.value}")
        return ParseNode(f"Type({token.value})")

    def parse_expression(self):
        # Expression -> FunctionCall | Identifier | Number
        token = self.current_token()
        if token.token_type == "NUMBER":
            self.consume("NUMBER")
            return ParseNode(f"Number({token.value})")
        elif token.token_type == "IDENTIFIER":
            id_node = ParseNode(f"Identifier({token.value})")
            self.consume("IDENTIFIER")
            if self.current_token() and self.current_token().value == '(':
                return self.parse_function_call(id_node)
            return id_node
        else:
            raise Exception(f"Unexpected token in expression: {token}")

    def parse_function_call(self, id_node):
        # FunctionCall -> Identifier '(' ArgumentList ')'
        self.consume("DELIMITER", "(")  # Consume '('
        args_node = self.parse_argument_list()
        self.consume("DELIMITER", ")")  # Consume ')'
        return ParseNode("FunctionCall", [id_node] + args_node)

    def parse_argument_list(self):
        # ArgumentList -> Expression ',' ArgumentList | Expression | ε
        args = []
        if self.current_token() and self.current_token().value != ')':  # Check for ε
            args.append(self.parse_expression())
            while self.current_token() and self.current_token().value == ',':
                self.consume("DELIMITER", ",")
                args.append(self.parse_expression())
        return args


# Example usage
tokens = Lexer("int main() { int x = 5; printf(x); }")
parser = Parser(tokens)
parse_tree = parser.parse_program()
print(parse_tree)
