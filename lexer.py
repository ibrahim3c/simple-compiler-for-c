import string
class Token:
    def __init__(self, token_type, value):
        self.token_type = token_type
        self.value = value

    def __repr__(self):
        return f"{self.value} ({self.token_type})"

# Helper functions
def is_punctuator(ch):
    return ch in string.punctuation or ch.isspace()

def valid_identifier(s):
    if not s:
        return False
    if s[0].isdigit() or is_punctuator(s[0]):
        return False
    return all(not is_punctuator(ch) for ch in s[1:])

def is_operator(ch):
    return ch in '+-*/><|&='

def is_keyword(s):
    keywords = {
        'if', 'else', 'while', 'do', 'break', 'continue', 'int', 'double',
        'float', 'return', 'char', 'case', 'long', 'short', 'typedef', 'switch',
        'unsigned', 'void', 'static', 'struct', 'sizeof', 'volatile', 'enum',
        'const', 'union', 'extern', 'bool'
    }
    return s in keywords

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

# Main Lexer function
def Lexer(s):
    tokens = []
    left = right = 0
    while right <= len(s) and left <= right:
        if right < len(s) and not is_punctuator(s[right]):
            right += 1
        elif right < len(s) and is_punctuator(s[right]) and left == right:
            # Check if it's an operator
            if is_operator(s[right]):
                tokens.append(Token("OPERATOR", s[right]))
            # Check if it's a delimiter
            elif s[right] in '(){};':
                tokens.append(Token("DELIMITER", s[right]))
            right += 1
            left = right
        elif (right == len(s) or is_punctuator(s[right])) and left != right:
            sub = s[left:right]
            # Keyword 
            if is_keyword(sub):
                tokens.append(Token("KEYWORD", sub))
            # Number 
            elif is_number(sub):
                tokens.append(Token("NUMBER", sub))
            # Valid identifier check
            elif valid_identifier(sub):
                tokens.append(Token("IDENTIFIER", sub))
            # Invalid identifier check
            else:
                tokens.append(Token("INVALID IDENTIFIER", sub))
            left = right
        else:
            right += 1
    return tokens

# Example usage
tokens = Lexer("int main() { int x = 5;  printf(x); }")
for token in tokens:
    print(token)
