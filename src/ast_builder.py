"""
ast_builder.py
===============
Tahap 3 (lanjutan): PARSE TREE -> AST

Modul ieu "nyaring" Parse Tree (CST) hasil parser.py jadi AST nu leuwih
basajan tur gampang diolah ku tahap Semantic Analysis, Optimizer, sarta
Code Generator. Simpul perantara grammar (kayaning term/factor/group/
logic_or/logic_and/dst.) digabungkeun jadi hiji simpul umum: BinOp/UnaryOp.
"""

from ast_nodes import (
    Program, VarDecl, Assign, IndexAssign, If, While, For, FuncDecl,
    Return, Break, Continue, Block, ExprStmt,
    BinOp, UnaryOp, Literal, Identifier, Call, Index, ArrayLiteral,
)

_BINARY_RULES = {"logic_or", "logic_and", "equality", "comparison", "term", "factor"}


def _literal_value(tok):
    if tok.type in ("INT", "FLOAT", "STRING"):
        return tok.value
    if tok.type == "BENER":
        return True
    if tok.type == "SALAH":
        return False
    if tok.type == "KOSONG":
        return None
    raise ValueError(f"Token literal teu dikenal: {tok.type}")


def convert_expr(node):
    rule = node.rule

    if rule == "literal":
        tok = node.children[0]
        return Literal(_literal_value(tok), line=tok.line)

    if rule == "identifier":
        tok = node.children[0]
        return Identifier(tok.value, line=tok.line)

    if rule == "group":
        return convert_expr(node.children[0])

    if rule == "array_literal":
        return ArrayLiteral([convert_expr(c) for c in node.children], line=node.line)

    if rule == "call_expr":
        callee = convert_expr(node.children[0])
        args = [convert_expr(c) for c in node.children[1:]]
        return Call(callee, args, line=node.line)

    if rule == "index_expr":
        obj = convert_expr(node.children[0])
        idx = convert_expr(node.children[1])
        return Index(obj, idx, line=node.line)

    if rule == "unary":
        op_tok, operand = node.children
        return UnaryOp(op_tok.type, convert_expr(operand), line=op_tok.line)

    if rule in _BINARY_RULES:
        left, op_tok, right = node.children
        return BinOp(op_tok.type, convert_expr(left), convert_expr(right), line=op_tok.line)

    raise ValueError(f"AST Builder: teu apal kumaha ngonversi ekspresi rule={rule!r}")


def convert_block(node):
    stmts = [convert_stmt(c) for c in node.children]
    return Block(stmts, line=node.line)


def convert_stmt(node):
    rule = node.rule

    if rule == "var_decl":
        ident, expr = node.children
        return VarDecl(ident.value, convert_expr(expr), line=ident.line)

    if rule == "assign_stmt":
        ident, expr = node.children
        return Assign(ident.value, convert_expr(expr), line=ident.line)

    if rule == "index_assign_stmt":
        index_node, rhs = node.children
        target = convert_expr(index_node)  # mangrupa Index(...)
        return IndexAssign(target.obj, target.index, convert_expr(rhs), line=node.line)

    if rule == "if_stmt":
        children = node.children
        cond = convert_expr(children[0])
        then_block = convert_block(children[1])
        elif_clauses = []
        else_block = None
        for c in children[2:]:
            if c.rule == "elif_clause":
                ec, eb = c.children
                elif_clauses.append((convert_expr(ec), convert_block(eb)))
            elif c.rule == "else_clause":
                else_block = convert_block(c.children[0])
        return If(cond, then_block, elif_clauses, else_block, line=node.line)

    if rule == "while_stmt":
        cond, body = node.children
        return While(convert_expr(cond), convert_block(body), line=node.line)

    if rule == "for_stmt":
        ident, iterable, body = node.children
        return For(ident.value, convert_expr(iterable), convert_block(body), line=ident.line)

    if rule == "func_decl":
        name, param_node, body = node.children
        params = [p.value for p in param_node.children]
        return FuncDecl(name.value, params, convert_block(body), line=name.line)

    if rule == "return_stmt":
        expr = convert_expr(node.children[0]) if node.children else None
        return Return(expr, line=node.line)

    if rule == "break_stmt":
        return Break(line=node.line)

    if rule == "continue_stmt":
        return Continue(line=node.line)

    if rule == "block":
        return convert_block(node)

    if rule == "expr_stmt":
        return ExprStmt(convert_expr(node.children[0]), line=node.line)

    raise ValueError(f"AST Builder: teu apal kumaha ngonversi statement rule={rule!r}")


def build_ast(parse_tree):
    assert parse_tree.rule == "program", "Akar Parse Tree kudu 'program'"
    statements = [convert_stmt(c) for c in parse_tree.children]
    return Program(statements, line=1)
