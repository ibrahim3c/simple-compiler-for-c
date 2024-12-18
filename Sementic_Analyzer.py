from lexer import Lexer
from parser import Parser

class SemanticError(Exception):
    """Custom exception for semantic analysis errors."""
    pass

class SymbolTable:
    def __init__(self, parent=None):
        """
        Initialize a symbol table with optional parent scope
        
        Args:
            parent (SymbolTable, optional): Parent scope symbol table
        """
        self.symbols = {}
        self.parent = parent

    def declare(self, name, type_name, is_function=False):
        """
        Declare a new symbol in the current scope
        
        Args:
            name (str): Symbol name
            type_name (str): Symbol type
            is_function (bool, optional): Whether symbol is a function
        
        Raises:
            SemanticError: If symbol is already declared in current scope
        """
        if name in self.symbols:
            raise SemanticError(f"Symbol '{name}' already declared in this scope")
        
        self.symbols[name] = {
            'type': type_name,
            'is_function': is_function
        }

    def lookup(self, name):
        """
        Look up a symbol, checking current and parent scopes
        
        Args:
            name (str): Symbol name to look up
        
        Returns:
            dict: Symbol information
        
        Raises:
            SemanticError: If symbol is not found
        """
        # Check current scope
        if name in self.symbols:
            return self.symbols[name]
        
        # Check parent scopes
        if self.parent:
            return self.parent.lookup(name)
        
        raise SemanticError(f"Undeclared symbol '{name}'")

class SemanticAnalyzer:
    def __init__(self, predefined_functions=None):
        """
        Initialize semantic analyzer with global symbol table
        
        Args:
            predefined_functions (dict, optional): Predefined functions with their signatures
        """
        self.global_symbol_table = SymbolTable()
        self.current_symbol_table = self.global_symbol_table
        
        # Default predefined functions if not provided
        default_functions = {
            'printf': {'type': 'int', 'is_function': True},
            'puts': {'type': 'int', 'is_function': True},
            'getchar': {'type': 'int', 'is_function': True},
            'scanf': {'type': 'int', 'is_function': True}
        }
        
        # Add predefined functions to global symbol table
        functions_to_add = predefined_functions or default_functions
        for name, info in functions_to_add.items():
            self.global_symbol_table.declare(name, info['type'], info['is_function'])

    def analyze(self, parse_tree):
        """
        Perform semantic analysis on the parse tree
        
        Args:
            parse_tree (ParseNode): Root of the parse tree
        
        Returns:
            SymbolTable: The global symbol table after analysis
        """
        self._analyze_node(parse_tree)
        return self.global_symbol_table

    def _analyze_node(self, node):
        """
        Recursively analyze each node in the parse tree
        
        Args:
            node (ParseNode): Current node to analyze
        """
        # Map of node name to analysis method
        analysis_methods = {
            'Program': self._analyze_program,
            'Function': self._analyze_function,
            'VariableDeclaration': self._analyze_variable_declaration,
            'FunctionCall': self._analyze_function_call,
            'ExpressionStatement': self._analyze_expression_statement
        }

        # Default to node's own method name if it exists, otherwise skip
        method = analysis_methods.get(node.name.split('(')[0], self._default_analysis)
        method(node)

    def _default_analysis(self, node):
        """
        Default analysis method that recursively analyzes children
        
        Args:
            node (ParseNode): Node to analyze
        """
        for child in node.children:
            self._analyze_node(child)

    def _analyze_program(self, node):
        """
        Analyze the entire program
        
        Args:
            node (ParseNode): Program node
        """
        for child in node.children:
            self._analyze_node(child)

    def _analyze_function(self, node):
        """
        Analyze function declaration
        
        Args:
            node (ParseNode): Function node
        
        Raises:
            SemanticError: If function is incorrectly defined
        """
        # First child is return type, second is function name
        return_type = node.children[0].name.split('(')[1].strip(')')
        func_name = node.children[1].name.split('(')[1].strip(')')

        # Create new scope for function body
        prev_symbol_table = self.current_symbol_table
        self.current_symbol_table = SymbolTable(parent=prev_symbol_table)

        # Declare function in parent scope
        prev_symbol_table.declare(func_name, return_type, is_function=True)

        # Analyze function body (third child is the declaration list)
        self._analyze_node(node.children[2])

        # Restore previous symbol table
        self.current_symbol_table = prev_symbol_table

    def _analyze_variable_declaration(self, node):
        """
        Analyze variable declaration
        
        Args:
            node (ParseNode): Variable declaration node
        
        Raises:
            SemanticError: If variable is improperly declared
        """
        # Extract type and identifier
        var_type = node.children[0].name.split('(')[1].strip(')')
        var_name = node.children[1].name.split('(')[1].strip(')')

        # Check for initialization
        if len(node.children) > 2:
            init_node = node.children[2]
            self._type_check_assignment(var_type, init_node)

        # Declare in current symbol table
        self.current_symbol_table.declare(var_name, var_type)

    def _analyze_function_call(self, node):
        """
        Analyze function call
        
        Args:
            node (ParseNode): Function call node
        
        Raises:
            SemanticError: If function is not declared or arguments are incorrect
        """
        # First child is function identifier
        func_name = node.children[0].name.split('(')[1].strip(')')
        
        try:
            # Verify function exists
            func_info = self.current_symbol_table.lookup(func_name)
            
            # Ensure it's actually a function
            if not func_info['is_function']:
                raise SemanticError(f"'{func_name}' is not a function")
        except SemanticError as e:
            raise SemanticError(f"Function call error: {str(e)}")

    def _analyze_expression_statement(self, node):
        """
        Analyze expression statement
        
        Args:
            node (ParseNode): Expression statement node
        """
        for child in node.children:
            self._analyze_node(child)

    def _type_check_assignment(self, expected_type, value_node):
        """
        Perform type checking for assignment
        
        Args:
            expected_type (str): Expected type of the variable
            value_node (ParseNode): Node representing the value being assigned
        
        Raises:
            SemanticError: If type mismatch occurs
        """
        # Handle different node types for type checking
        if value_node.name.startswith('Number'):
            value_type = self._infer_number_type(value_node)
            if not self._is_compatible_type(expected_type, value_type):
                raise SemanticError(f"Type mismatch: cannot assign {value_type} to {expected_type}")
        
        elif value_node.name.startswith('Identifier'):
            var_name = value_node.name.split('(')[1].strip(')')
            try:
                var_info = self.current_symbol_table.lookup(var_name)
                if not self._is_compatible_type(expected_type, var_info['type']):
                    raise SemanticError(f"Type mismatch: cannot assign {var_info['type']} to {expected_type}")
            except SemanticError as e:
                raise SemanticError(f"Assignment error: {str(e)}")

    def _infer_number_type(self, number_node):
        """
        Infer the type of a number node
        
        Args:
            number_node (ParseNode): Number node
        
        Returns:
            str: Inferred type (int, float, double)
        """
        value = number_node.name.split('(')[1].strip(')')
        try:
            int(value)
            return 'int'
        except ValueError:
            try:
                float(value)
                return 'double'  # Default to double for floating-point
            except ValueError:
                raise SemanticError(f"Invalid number: {value}")

    def _is_compatible_type(self, type1, type2):
        """
        Check type compatibility
        
        Args:
            type1 (str): First type
            type2 (str): Second type
        
        Returns:
            bool: Whether types are compatible
        """
        # Simplistic type compatibility (can be expanded)
        compatible_types = {
            'int': ['int'],
            'float': ['int', 'float'],
            'double': ['int', 'float', 'double'],
            'char': ['char']
        }
        return type2 in compatible_types.get(type1, [])

# Example usage
def semantic_analysis_example(parser, predefined_functions=None):
    """
    Perform semantic analysis on a parser's parse tree
    
    Args:
        parser (Parser): Parser with tokens
        predefined_functions (dict, optional): Additional predefined functions
    
    Returns:
        SymbolTable: Symbol table after analysis
    """
    semantic_analyzer = SemanticAnalyzer(predefined_functions)
    
    try:
        symbol_table = semantic_analyzer.analyze(parser.parse_program())
        print("Semantic Analysis Successful")
        
        # Optional: Print symbol table contents
        # print("\nSymbol Table:")
        # for name, info in symbol_table.symbols.items():
        #     print(f"{name}: {info}")
        
        # return symbol_table
    
    except SemanticError as e:
        print(f"Semantic Analysis Failed: {e}")
        return None

# Demonstration
def main():
    # Tokenize and parse the input
    tokens = Lexer("int main() { int x = 5; printf(x); }")
    parser = Parser(tokens)
    
    # Perform semantic analysis
    semantic_analysis_example(parser)

if __name__ == "__main__":
    main()