"""
parser.py
==========
Tahap 2: PARSER (ANALISIS SINTAKSIS) -> PARSE TREE

Parser ieu nganggo metode "Recursive Descent" nuturkeun grammar (EBNF)
basa SUNDAC (tingali docs/README.md kanggo grammar lengkepna).

Kaluaran tina tahap ieu nyaeta PARSE TREE (Concrete Syntax Tree / CST):
hiji wangun tangkal nu struktur-na 1:1 nuturkeun aturan grammar.
Parse Tree ieu engke bakal "disederhanakeun" jadi AST ku ast_builder.py.

Grammar ringkes:
    program     -> statement* EOF
    statement   -> var_decl | assign_stmt | if_stmt | while_stmt
                 | for_stmt | func_decl | return_stmt | break_stmt
                 | continue_stmt | block | expr_stmt
    var_decl    -> SIMPEN IDENT ASSIGN expression SEMI
    assign_stmt -> (IDENT | index_target) ASSIGN expression SEMI
    if_stmt     -> UPAMA LPAREN expression RPAREN block
                   (SABALIKNA UPAMA LPAREN expression RPAREN block)*
                   (SABALIKNA block)?
    while_stmt  -> SALILA LPAREN expression RPAREN block
    for_stmt    -> PIKEUN IDENT DINA expression block
    func_decl   -> PANCEN IDENT LPAREN param_list? RPAREN block
    return_stmt -> BALIKKEUN expression? SEMI
    break_stmt  -> EUREUN SEMI
    continue_stmt -> TULUYKEUN SEMI
    block       -> LBRACE statement* RBRACE
    expression  -> logic_or
    logic_or    -> logic_and (ATAWA logic_and)*
    logic_and   -> equality (JEUNG equality)*
    equality    -> comparison ((EQ|NEQ) comparison)*
    comparison  -> term ((LT|GT|LTE|GTE) term)*
    term        -> factor ((PLUS|MINUS) factor)*
    factor      -> unary ((KALI|BAGI|MODULO) unary)*
    unary       -> (HENTEU|MINUS) unary | call
    call        -> primary (LPAREN args? RPAREN | LBRACKET expression RBRACKET)*
    primary     -> INT | FLOAT | STRING | BENER | SALAH | KOSONG
                 | IDENT | LPAREN expression RPAREN | array_literal
    array_literal -> LBRACKET (expression (COMMA expression)*)? RBRACKET
"""

from errors import ParserError


class ParseTreeNode:
    """Hiji simpul (node) dina Parse Tree / Concrete Syntax Tree."""

    def __init__(self, rule, children=None, line=None):
        self.rule = rule              # ngaran aturan grammar, cth: "if_stmt"
        self.children = children or []  # eusi-na: ParseTreeNode atawa Token
        self.line = line

    def pretty(self, depth=0):
        pad = "  " * depth
        out = [f"{pad}<{self.rule}>"]
        for c in self.children:
            if isinstance(c, ParseTreeNode):
                out.append(c.pretty(depth + 1))
            else:  # Token
                out.append(f"{pad}  {c.type}: {c.value!r}")
        return "\n".join(out)

    def __repr__(self):
        return f"ParseTreeNode({self.rule}, {len(self.children)} children)"


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # -- util -----------------------------------------------------------
    def _peek(self, offset=0):
        i = min(self.pos + offset, len(self.tokens) - 1)
        return self.tokens[i]

    def _check(self, *types):
        return self._peek().type in types

    def _advance(self):
        tok = self.tokens[self.pos]
        if tok.type != "EOF":
            self.pos += 1
        return tok

    def _match(self, *types):
        if self._check(*types):
            return self._advance()
        return None

    def _expect(self, type_, msg=None):
        if self._check(type_):
            return self._advance()
        tok = self._peek()
        raise ParserError(
            msg or f"Dipiharep '{type_}' tapi anu kapanggih '{tok.type}' ({tok.value!r})",
            tok.line, tok.col,
        )

    # -- entry point ------------------------------------------------------
    def parse(self):
        statements = []
        while not self._check("EOF"):
            statements.append(self._statement())
        return ParseTreeNode("program", statements, line=1)

    # -- statements ---------------------------------------------------------
    def _statement(self):
        tok = self._peek()
        if tok.type == "SIMPEN":
            return self._var_decl()
        if tok.type == "UPAMA":
            return self._if_stmt()
        if tok.type == "SALILA":
            return self._while_stmt()
        if tok.type == "PIKEUN":
            return self._for_stmt()
        if tok.type == "PANCEN":
            return self._func_decl()
        if tok.type == "BALIKKEUN":
            return self._return_stmt()
        if tok.type == "EUREUN":
            self._advance()
            self._expect("SEMI", "Dipiharep ';' sanggeus EUREUN")
            return ParseTreeNode("break_stmt", [], line=tok.line)
        if tok.type == "TULUYKEUN":
            self._advance()
            self._expect("SEMI", "Dipiharep ';' sanggeus TULUYKEUN")
            return ParseTreeNode("continue_stmt", [], line=tok.line)
        if tok.type == "LBRACE":
            return self._block()

        # assignment ATAWA expression statement -- kudu dipeuncitkeun ku lookahead
        if tok.type == "IDENTIFIER":
            save = self.pos
            ident = self._advance()
            # target basajan: IDENT '='
            if self._check("ASSIGN"):
                self._advance()
                expr = self._expression()
                self._expect("SEMI", "Dipiharep ';' sanggeus assignment")
                return ParseTreeNode("assign_stmt", [ident, expr], line=ident.line)
            # target indeks: IDENT '[' expr ']' '='
            if self._check("LBRACKET"):
                self.pos = save
                expr_node = self._call()
                if self._check("ASSIGN") and expr_node.rule == "index_expr":
                    self._advance()
                    rhs = self._expression()
                    self._expect("SEMI", "Dipiharep ';' sanggeus assignment indeks")
                    return ParseTreeNode("index_assign_stmt", [expr_node, rhs], line=ident.line)
                # lain assignment, mung expression statement biasa
                self._expect("SEMI", "Dipiharep ';' sanggeus statement")
                return ParseTreeNode("expr_stmt", [expr_node], line=ident.line)
            # sanes assignment -> balikkeun deui pos, bener-bener expr_stmt
            self.pos = save

        expr = self._expression()
        self._expect("SEMI", "Dipiharep ';' sanggeus statement")
        return ParseTreeNode("expr_stmt", [expr], line=expr.line)

    def _var_decl(self):
        kw = self._advance()  # SIMPEN
        ident = self._expect("IDENTIFIER", "Dipiharep ngaran variabel sanggeus SIMPEN")
        self._expect("ASSIGN", "Dipiharep '=' dina deklarasi variabel")
        expr = self._expression()
        self._expect("SEMI", "Dipiharep ';' sanggeus deklarasi variabel")
        return ParseTreeNode("var_decl", [ident, expr], line=kw.line)

    def _if_stmt(self):
        kw = self._advance()  # UPAMA
        self._expect("LPAREN", "Dipiharep '(' sanggeus UPAMA")
        cond = self._expression()
        self._expect("RPAREN", "Dipiharep ')' sanggeus kondisi UPAMA")
        then_block = self._block()
        children = [cond, then_block]

        while self._check("SABALIKNA") and self._peek(1).type == "UPAMA":
            self._advance(); self._advance()  # SABALIKNA UPAMA
            self._expect("LPAREN")
            elif_cond = self._expression()
            self._expect("RPAREN")
            elif_block = self._block()
            children.append(ParseTreeNode("elif_clause", [elif_cond, elif_block]))

        if self._check("SABALIKNA"):
            self._advance()
            else_block = self._block()
            children.append(ParseTreeNode("else_clause", [else_block]))

        return ParseTreeNode("if_stmt", children, line=kw.line)

    def _while_stmt(self):
        kw = self._advance()  # SALILA
        self._expect("LPAREN", "Dipiharep '(' sanggeus SALILA")
        cond = self._expression()
        self._expect("RPAREN", "Dipiharep ')' sanggeus kondisi SALILA")
        body = self._block()
        return ParseTreeNode("while_stmt", [cond, body], line=kw.line)

    def _for_stmt(self):
        kw = self._advance()  # PIKEUN
        ident = self._expect("IDENTIFIER", "Dipiharep ngaran variabel sanggeus PIKEUN")
        self._expect("DINA", "Dipiharep 'DINA' dina perulangan PIKEUN")
        iterable = self._expression()
        body = self._block()
        return ParseTreeNode("for_stmt", [ident, iterable, body], line=kw.line)

    def _func_decl(self):
        kw = self._advance()  # PANCEN
        name = self._expect("IDENTIFIER", "Dipiharep ngaran pancen (fungsi)")
        self._expect("LPAREN", "Dipiharep '(' sanggeus ngaran pancen")
        params = []
        if not self._check("RPAREN"):
            params.append(self._expect("IDENTIFIER", "Dipiharep parameter"))
            while self._match("COMMA"):
                params.append(self._expect("IDENTIFIER", "Dipiharep parameter"))
        self._expect("RPAREN", "Dipiharep ')' sanggeus daptar parameter")
        body = self._block()
        param_node = ParseTreeNode("param_list", params)
        return ParseTreeNode("func_decl", [name, param_node, body], line=kw.line)

    def _return_stmt(self):
        kw = self._advance()  # BALIKKEUN
        if self._check("SEMI"):
            self._advance()
            return ParseTreeNode("return_stmt", [], line=kw.line)
        expr = self._expression()
        self._expect("SEMI", "Dipiharep ';' sanggeus BALIKKEUN")
        return ParseTreeNode("return_stmt", [expr], line=kw.line)

    def _block(self):
        brace = self._expect("LBRACE", "Dipiharep '{' pikeun mimitian blok")
        statements = []
        while not self._check("RBRACE", "EOF"):
            statements.append(self._statement())
        self._expect("RBRACE", "Dipiharep '}' pikeun nutup blok")
        return ParseTreeNode("block", statements, line=brace.line)

    # -- expressions (precedence climbing) ---------------------------------
    def _expression(self):
        return self._logic_or()

    def _logic_or(self):
        node = self._logic_and()
        while self._check("ATAWA"):
            op = self._advance()
            rhs = self._logic_and()
            node = ParseTreeNode("logic_or", [node, op, rhs], line=node.line)
        return node

    def _logic_and(self):
        node = self._equality()
        while self._check("JEUNG"):
            op = self._advance()
            rhs = self._equality()
            node = ParseTreeNode("logic_and", [node, op, rhs], line=node.line)
        return node

    def _equality(self):
        node = self._comparison()
        while self._check("EQ", "NEQ"):
            op = self._advance()
            rhs = self._comparison()
            node = ParseTreeNode("equality", [node, op, rhs], line=node.line)
        return node

    def _comparison(self):
        node = self._term()
        while self._check("LT", "GT", "LTE", "GTE"):
            op = self._advance()
            rhs = self._term()
            node = ParseTreeNode("comparison", [node, op, rhs], line=node.line)
        return node

    def _term(self):
        node = self._factor()
        while self._check("PLUS", "MINUS"):
            op = self._advance()
            rhs = self._factor()
            node = ParseTreeNode("term", [node, op, rhs], line=node.line)
        return node

    def _factor(self):
        node = self._unary()
        while self._check("KALI", "BAGI", "MODULO"):
            op = self._advance()
            rhs = self._unary()
            node = ParseTreeNode("factor", [node, op, rhs], line=node.line)
        return node

    def _unary(self):
        if self._check("HENTEU", "MINUS", "NOT_SYM"):
            op = self._advance()
            operand = self._unary()
            return ParseTreeNode("unary", [op, operand], line=op.line)
        return self._call()

    def _call(self):
        node = self._primary()
        while True:
            if self._check("LPAREN"):
                self._advance()
                args = []
                if not self._check("RPAREN"):
                    args.append(self._expression())
                    while self._match("COMMA"):
                        args.append(self._expression())
                self._expect("RPAREN", "Dipiharep ')' sanggeus daptar argumen")
                node = ParseTreeNode("call_expr", [node] + args, line=node.line)
            elif self._check("LBRACKET"):
                self._advance()
                index = self._expression()
                self._expect("RBRACKET", "Dipiharep ']' sanggeus indeks")
                node = ParseTreeNode("index_expr", [node, index], line=node.line)
            else:
                break
        return node

    def _primary(self):
        tok = self._peek()
        if tok.type in ("INT", "FLOAT", "STRING", "BENER", "SALAH", "KOSONG"):
            self._advance()
            return ParseTreeNode("literal", [tok], line=tok.line)
        if tok.type == "IDENTIFIER":
            self._advance()
            return ParseTreeNode("identifier", [tok], line=tok.line)
        if tok.type == "LPAREN":
            self._advance()
            expr = self._expression()
            self._expect("RPAREN", "Dipiharep ')' nutup tanda kurung")
            return ParseTreeNode("group", [expr], line=tok.line)
        if tok.type == "LBRACKET":
            self._advance()
            items = []
            if not self._check("RBRACKET"):
                items.append(self._expression())
                while self._match("COMMA"):
                    items.append(self._expression())
            self._expect("RBRACKET", "Dipiharep ']' nutup larik (array)")
            return ParseTreeNode("array_literal", items, line=tok.line)

        raise ParserError(
            f"Statement/ekspresi teu sah, kapanggih token '{tok.type}' ({tok.value!r})",
            tok.line, tok.col,
        )


def parse_tokens(tokens):
    return Parser(tokens).parse()
