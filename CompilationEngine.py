#!/usr/bin/python3
from JackTokenizer import Token, Tokenizer
from textwrap import indent


class peekable():

    def __init__(self, iterable):
        self.iterator = iter(iterable)
        self.cached = None

    def peek(self):
        if self.cached is None:
            self.cached = next(self.iterator)
            return self.cached
        else:
            return self.cached

    def __next__(self):
        if self.cached is None:
            return next(self.iterator)
        else:
            temp = self.cached
            self.cached = None
            return temp


class Compiler():

    def __init__(self, tokenizer):
        self.statementHandlers = {
            "let": self.compileLet,
            "if": self.compileIf,
            "while": self.compileWhile,
            "do": self.compileDo,
            "return": self.compileReturn
        }
        self.outURI = tokenizer.getOutURI()
        self.tokenizer = tokenizer
        compiled = self.compileClass(peekable(tokenizer.getTokens()))
        with open(self.outURI, "w+") as outFile:
            outFile.write(compiled)

    def compileClass(self, tokenIterator):
        'Compiles 1 class definition'
        # grammar ="class" "identifier" "{" classVarDec* subroutineDec* "}"
        output = (f"{next(tokenIterator)}\n"  # keyword class
                  f"{next(tokenIterator)}\n"  # identifier classname
                  f"{next(tokenIterator)}\n"  # symbol {
                  )
        # classVarDec's
        while (tokenIterator.peek().stringVal.lower() in ("static", "field")):
            output += f"{self.compileClassVarDec(tokenIterator)}\n"
        # subroutine's
        while (tokenIterator.peek().stringVal.lower() in ("constructor", "function", "method")):
            output += f"{self.compileSubroutine(tokenIterator)}\n"

        output += f"{next(tokenIterator)}\n"  # symbol }

        return f"<class>\n{indent(output, '  ')}</class>\n"

    def compileClassVarDec(self, tokenIterator):
        'Compiles any number of class variable declarations, starting with static or field and ending in a semicolon'
        # grammar = ('static'|'field') type varName (, varName) ;
        output = (f"{next(tokenIterator)}\n"  # ('static'|'field')
                  f"{next(tokenIterator)}\n"  # type
                  f"{next(tokenIterator)}\n"  # varName
                  )

        while (tokenIterator.peek().stringVal.lower() in (",")):
            output += f"{next(tokenIterator)}\n"  # ,
            output += f"{next(tokenIterator)}\n"  # varName

        output += f"{next(tokenIterator)}\n"  # ;
        return f"""<classVarDec>\n{indent(output, '  ')}</classVarDec>"""

    def compileSubroutine(self, tokenIterator):
        # grammar = ('constructor'|'function'|'method') ('void'|type) subroutineName '(' parameterList ')' subRoutineBody
        # ('constructor'|'function'|'method')
        output = f"{next(tokenIterator)}\n"
        output += f"{next(tokenIterator)}\n"  # ('void'|type)
        output += f"{next(tokenIterator)}\n"  # subroutineName
        output += f"{next(tokenIterator)}\n"  # '('
        # parameterList
        output += f"{self.compileParameterList(tokenIterator)}\n"
        output += f"{next(tokenIterator)}\n"  # ')'
        output += f"{self.compileSubroutineBody(tokenIterator)}\n"
        return f"""<subroutineDec>\n{indent(output, '  ')}</subroutineDec>"""

    def compileSubroutineBody(self, tokenIterator):
        # grammar = '{' varDec* statements '}'
        output = f"{next(tokenIterator)}\n"  # '{'
        # subroutineBody
        while (tokenIterator.peek().stringVal.lower() in ("var")):  # varDec*
            output += f"{self.compileVarDec(tokenIterator)}\n"

        output += f"{self.compileStatements(tokenIterator)}\n"  # statements
        output += f"{next(tokenIterator)}\n"  # '}'
        return f"""<subroutineBody>\n{indent(output, '  ')}</subroutineBody>"""

    def compileStatements(self, tokenIterator):
        output = ""
        while (tokenIterator.peek().stringVal.lower() in self.statementHandlers):
            output += self.statementHandlers[tokenIterator.peek().stringVal.lower()
                                        ](tokenIterator) + "\n"
        return f"""<statements>\n{indent(output, '  ')}</statements>"""

    def compileParameterList(self, tokenIterator):
        # grammar = ((type Varname) (',' type varName)*)?
        output = ""
        parameters = 0
        while (not tokenIterator.peek().stringVal.lower() == ")"):
            if (parameters > 0):
                output += f"{next(tokenIterator)}\n"  # ,
            output += f"{next(tokenIterator)}\n"  # type
            output += f"{next(tokenIterator)}\n"  # varName
            parameters += 1
        return f"""<parameterList>\n{indent(output, '  ')}</parameterList>"""

    def compileVarDec(self, tokenIterator):
        # grammar = 'var' type varName (, varName) ;
        output = (f"{next(tokenIterator)}\n"  # 'var'
                  f"{next(tokenIterator)}\n"  # type
                  f"{next(tokenIterator)}\n"  # varName
                  )

        while (tokenIterator.peek().stringVal.lower() in (",")):
            output += f"{next(tokenIterator)}\n"  # ,
            output += f"{next(tokenIterator)}\n"  # varName

        output += f"{next(tokenIterator)}\n"  # ;

        return f"""<varDec>\n{indent(output, '  ')}</varDec>"""

    def compileDo(self, tokenIterator):
        # grammar = 'do' subroutineCall ';'
        output = f"{next(tokenIterator)}\n"  # 'do'
        output += f"{self.compilesubroutineCall(tokenIterator)}" # subroutineCall
        output += f"{next(tokenIterator)}\n"  # ';'
        
        return f"""<doStatement>\n{indent(output, '  ')}</doStatement>"""

    def compilesubroutineCall(self, tokenIterator):
        # grammar = subroutineName'('expressionList')' | (className|varName)'.'subroutineName'('expressionList')'
        output = f"{next(tokenIterator)}\n"  # subroutineName className or varName

        if tokenIterator.peek().stringVal.lower() in ("."):
            output += f"{next(tokenIterator)}\n"  # '.'
            output += f"{next(tokenIterator)}\n"  # subroutineName

        output += f"{next(tokenIterator)}\n"  # '('
        output += f"{self.compileExpressionList(tokenIterator)}\n"  # expressionList
        output += f"{next(tokenIterator)}\n"  # ')'
        return output

    def compileLet(self, tokenIterator):
        # grammar = 'let' varName ('['expression']')? '=' expression ';'
        output = f"{next(tokenIterator)}\n"  # 'let'
        output += f"{next(tokenIterator)}\n"  # varName
        
        if tokenIterator.peek().stringVal.lower() in ("["):
            output += f"{next(tokenIterator)}\n"  # '['
            output += f"{self.compileExpression(tokenIterator)}\n"  # expression
            output += f"{next(tokenIterator)}\n"  # ']'

        output += f"{next(tokenIterator)}\n"  # '='
        output += f"{self.compileExpression(tokenIterator)}\n"  # expression
        output += f"{next(tokenIterator)}\n"  # ';'
        return f"""<letStatement>\n{indent(output, '  ')}</letStatement>"""
        
    def compileWhile(self, tokenIterator):
        output = f"{next(tokenIterator)}\n"  # 'while'
        output += f"{next(tokenIterator)}\n"  # '('
        output += f"{self.compileExpression(tokenIterator)}\n"  # expression
        output += f"{next(tokenIterator)}\n"  # ')'
        output += f"{next(tokenIterator)}\n"  # '{'
        output += f"{self.compileStatements(tokenIterator)}\n"  # statements
        output += f"{next(tokenIterator)}\n"  # '}'
        return f"""<whileStatement>\n{indent(output, '  ')}</whileStatement>"""

    def compileReturn(self, tokenIterator):
        # grammar = 'return' expression? ';'
        output = f"{next(tokenIterator)}\n"  # 'return'

        if tokenIterator.peek().stringVal.lower() not in (";"):
            output += f"{self.compileExpression(tokenIterator)}\n"  # expression

        output += f"{next(tokenIterator)}\n"  # ;
        
        return f"<returnStatement>\n{indent(output, '  ')}</returnStatement>"

    def compileIf(self, tokenIterator):
        output = f"{next(tokenIterator)}\n"  # 'if'
        output += f"{next(tokenIterator)}\n"  # '('
        output += f"{self.compileExpression(tokenIterator)}\n"  # expression
        output += f"{next(tokenIterator)}\n"  # ')'
        output += f"{next(tokenIterator)}\n"  # '{'
        output += f"{self.compileStatements(tokenIterator)}\n"  # statements
        output += f"{next(tokenIterator)}\n"  # '}'
        
        if tokenIterator.peek().stringVal.lower() in ("else"):
            output += f"{next(tokenIterator)}\n"  # 'else'
            output += f"{next(tokenIterator)}\n"  # '{'
            output += f"{self.compileStatements(tokenIterator)}\n"  # statements
            output += f"{next(tokenIterator)}\n"  # '}'

        return f"""<ifStatement>\n{indent(output, '  ')}</ifStatement>"""

    def compileExpression(self, tokenIterator):
        # grammar = term (op term)*
        output = f"{self.compileTerm(tokenIterator)}\n"  # term

        while tokenIterator.peek().stringVal.lower() in ("+","-","*","/","&","|","<",">","="):
            output += f"{next(tokenIterator)}\n"  # op
            output += f"{self.compileTerm(tokenIterator)}\n"  # term
        
        return f"<expression>\n{indent(output, '  ')}</expression>"

    def compileTerm(self, tokenIterator):
        # grammar = integerConstant|stringconstant|keywordConstant|varName|varName'['expression']'|subRoutineCall|'('expression')'|unaryOp term
        peek = tokenIterator.peek().stringVal.lower()
        output = ""
        if peek in ("~", "-"): # unaryOp term
            output += f"{next(tokenIterator)}\n"  # unaryOp ~ or -
            output += f"{self.compileTerm(tokenIterator)}\n"  # term
        elif peek in ("("):
            output += f"{next(tokenIterator)}\n"  # '('
            output += f"{self.compileExpression(tokenIterator)}\n"  # expression
            output += f"{next(tokenIterator)}\n"  # ')'
        else:
            output += f"{next(tokenIterator)}\n"  # integerConstant, stringConstant, keywordConstant, varName, or subroutineCall
            peek = tokenIterator.peek().stringVal.lower()
            if peek in (".", "("): # subroutineCall
                if peek in ("."):
                    output += f"{next(tokenIterator)}\n"  # '.'
                    output += f"{next(tokenIterator)}\n"  # subroutineName

                output += f"{next(tokenIterator)}\n"  # '('
                output += f"{self.compileExpressionList(tokenIterator)}\n"  # expression
                output += f"{next(tokenIterator)}\n"  # ')'
            elif peek in ("["): # array access
                output += f"{next(tokenIterator)}\n"  # '['
                output += f"{self.compileExpression(tokenIterator)}\n"  # expression
                output += f"{next(tokenIterator)}\n"  # ']'


        return f"<term>\n{indent(output, '  ')}</term>"

    def compileExpressionList(self, tokenIterator):
        # grammar = (expression (',' expression)*)?
        output = ""
        parameters = 0
        while tokenIterator.peek().stringVal.lower() not in (")") or tokenIterator.peek().tokenType == "stringConstant":
            if (parameters > 0):
                output += f"{next(tokenIterator)}\n"  # ,
            output += f"{self.compileExpression(tokenIterator)}\n"  # expression
            parameters += 1
        
        return f"<expressionList>\n{indent(output, '  ')}</expressionList>"
