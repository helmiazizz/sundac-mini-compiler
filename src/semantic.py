"""
semantic.py
============
Tahap 4: SEMANTIC ANALYSIS (ANALISIS SEMANTIK)

Tahap ieu moal meriksa "tata basa" deui (éta tugas Parser), tapi
meriksa "harti/logika" tina program, contona:
  - Variabel kudu dideklarasikeun (SIMPEN) saméméh dipaké.
  - Teu meunang ngadeklarasikeun variabel/pancen anu sarua dua kali
    dina ruang lingkup (scope) anu sarua.
  - BALIKKEUN (return) ngan sah di jero PANCEN.
  - EUREUN/TULUYKEUN (break/continue) ngan sah di jero perulangan.
  - Jumlah argumen waktu manggil pancen kudu cocog jeung parameter-na.

Modul ieu ngabangun TABEL SIMBOL (symbol table) sacara dinamis bari
napel (traverse) kana AST, sarta ngumpulkeun sadaya kasalahan
(teu eureun dina kasalahan kahiji, sangkan sakabéh kasalahan bisa
dilaporkeun sakaligus -- kawas kompiler beneran).
"""

from ast_nodes import (
    Program, VarDecl, Assign, IndexAssign, If, While, For, FuncDecl,
    Return, Break, Continue, Block, ExprStmt,
    BinOp, UnaryOp, Literal, Identifier, Call, Index, ArrayLiteral,
)
from lexer import BUILTIN_FUNCTIONS
from errors import SemanticError


class Scope:
    """Hiji ruang lingkup (scope) -- bagian tina Tabel Simbol."""

    def __init__(self, kind, parent=None):
        self.kind = kind          # "global" atawa "function"
        self.parent = parent
        self.symbols = {}         # name -> dict(info)

    def declare(self, name, info):
        self.symbols[name] = info

    def declared_locally(self, name):
        return name in self.symbols

    def resolve(self, name):
        scope = self
        while scope is not None:
            if name in scope.symbols:
                return scope.symbols[name]
            scope = scope.parent
        return None


class SemanticAnalyzer:
    def __init__(self):
        self.errors = []
        self.global_scope = Scope("global")
        self.loop_depth = 0
        self.func_stack = []

    # -- API umum -----------------------------------------------------
    def analyze(self, program: Program):
        self._predeclare_funcs(program.statements, self.global_scope)
        for stmt in program.statements:
            self.visit_stmt(stmt, self.global_scope)
        return self.errors

    def error(self, msg, line):
        self.errors.append(SemanticError(msg, line))

    # -- pra-deklarasi pancen (sangkan bisa silih panggil / forward ref) --
    def _predeclare_funcs(self, statements, scope):
        for stmt in statements:
            if isinstance(stmt, FuncDecl):
                if scope.declared_locally(stmt.name):
                    self.error(
                        f"Pancen '{stmt.name}' geus didefinisikeun saméméhna "
                        f"dina ruang lingkup nu sarua", stmt.line)
                else:
                    scope.declare(stmt.name, {
                        "kind": "func", "params": stmt.params, "line": stmt.line,
                    })

    def visit_block(self, block, scope):
        self._predeclare_funcs(block.statements, scope)
        for stmt in block.statements:
            self.visit_stmt(stmt, scope)

    # -- statement ------------------------------------------------------
    def visit_stmt(self, stmt, scope):
        method = getattr(self, f"visit_{type(stmt).__name__}", None)
        if method is None:
            self.error(f"Statement teu dikenal: {type(stmt).__name__}", getattr(stmt, "line", 0))
            return
        method(stmt, scope)

    def visit_VarDecl(self, node, scope):
        self.visit_expr(node.expr, scope)
        if scope.declared_locally(node.name):
            self.error(
                f"Variabel '{node.name}' geus aya dina ruang lingkup ieu "
                f"(lamun rék ngarobah nilai, teu kudu nulis SIMPEN deui)", node.line)
        scope.declare(node.name, {"kind": "var", "line": node.line})

    def visit_Assign(self, node, scope):
        self.visit_expr(node.expr, scope)
        info = scope.resolve(node.name)
        if info is None:
            self.error(
                f"Variabel '{node.name}' teu acan dideklarasikeun "
                f"(pake 'SIMPEN {node.name} = ...' heula)", node.line)
        elif info["kind"] == "func":
            self.error(f"'{node.name}' nyaeta ngaran pancen, teu bisa dipake jadi variabel", node.line)

    def visit_IndexAssign(self, node, scope):
        self.visit_expr(node.obj, scope)
        self.visit_expr(node.index, scope)
        self.visit_expr(node.value, scope)

    def visit_If(self, node, scope):
        self.visit_expr(node.cond, scope)
        self.visit_block(node.then_block, scope)
        for cond, block in node.elif_clauses:
            self.visit_expr(cond, scope)
            self.visit_block(block, scope)
        if node.else_block is not None:
            self.visit_block(node.else_block, scope)

    def visit_While(self, node, scope):
        self.visit_expr(node.cond, scope)
        self.loop_depth += 1
        self.visit_block(node.body, scope)
        self.loop_depth -= 1

    def visit_For(self, node, scope):
        self.visit_expr(node.iterable, scope)
        scope.declare(node.var_name, {"kind": "var", "line": node.line})
        self.loop_depth += 1
        self.visit_block(node.body, scope)
        self.loop_depth -= 1

    def visit_FuncDecl(self, node, scope):
        func_scope = Scope("function", parent=scope)
        seen_params = set()
        for p in node.params:
            if p in seen_params:
                self.error(f"Parameter '{p}' diulang dina pancen '{node.name}'", node.line)
            seen_params.add(p)
            func_scope.declare(p, {"kind": "param", "line": node.line})
        self.func_stack.append(node)
        self.visit_block(node.body, func_scope)
        self.func_stack.pop()

    def visit_Return(self, node, scope):
        if not self.func_stack:
            self.error("BALIKKEUN (return) ngan sah dipake di jero PANCEN (fungsi)", node.line)
        if node.expr is not None:
            self.visit_expr(node.expr, scope)

    def visit_Break(self, node, scope):
        if self.loop_depth == 0:
            self.error("EUREUN (break) ngan sah dipake di jero perulangan SALILA/PIKEUN", node.line)

    def visit_Continue(self, node, scope):
        if self.loop_depth == 0:
            self.error("TULUYKEUN (continue) ngan sah dipake di jero perulangan SALILA/PIKEUN", node.line)

    def visit_Block(self, node, scope):
        self.visit_block(node, scope)

    def visit_ExprStmt(self, node, scope):
        self.visit_expr(node.expr, scope)

    # -- expression -------------------------------------------------------
    def visit_expr(self, node, scope):
        if isinstance(node, Literal):
            return
        if isinstance(node, Identifier):
            if scope.resolve(node.name) is None:
                self.error(
                    f"Variabel '{node.name}' teu acan dideklarasikeun "
                    f"(pake 'SIMPEN {node.name} = ...' heula)", node.line)
            return
        if isinstance(node, BinOp):
            self.visit_expr(node.left, scope)
            self.visit_expr(node.right, scope)
            return
        if isinstance(node, UnaryOp):
            self.visit_expr(node.operand, scope)
            return
        if isinstance(node, ArrayLiteral):
            for el in node.elements:
                self.visit_expr(el, scope)
            return
        if isinstance(node, Index):
            self.visit_expr(node.obj, scope)
            self.visit_expr(node.index, scope)
            return
        if isinstance(node, Call):
            self._check_call(node, scope)
            return
        self.error(f"Ekspresi teu dikenal: {type(node).__name__}", getattr(node, "line", 0))

    def _check_call(self, node, scope):
        if isinstance(node.callee, Identifier):
            name = node.callee.name
            if name in BUILTIN_FUNCTIONS:
                pass  # fungsi bawaan -- arity teu dicek sangkan fleksibel
            else:
                info = scope.resolve(name)
                if info is None:
                    self.error(
                        f"Pancen '{name}' teu dikenal (lain fungsi bawaan Basa Sunda, "
                        f"lain ogé didefinisikeun ku PANCEN)", node.line)
                elif info["kind"] != "func":
                    self.error(f"'{name}' lain pancen, teu bisa dipanggil kawas fungsi", node.line)
                else:
                    expected, got = len(info["params"]), len(node.args)
                    if expected != got:
                        self.error(
                            f"Pancen '{name}' meryogikeun {expected} argumen, "
                            f"tapi anu dibikeun {got}", node.line)
        else:
            self.visit_expr(node.callee, scope)

        for a in node.args:
            self.visit_expr(a, scope)


def analyze_program(program: Program):
    """Mulangkeun (raises) SemanticError munggaran lamun aya error,
    sarta mulangkeun objek SemanticAnalyzer (pikeun tabel simbol) lamun bersih."""
    analyzer = SemanticAnalyzer()
    errors = analyzer.analyze(program)
    if errors:
        raise errors[0] if len(errors) == 1 else SemanticError(
            "Kapanggih " + str(len(errors)) + " kasalahan:\n" +
            "\n".join(f"  - {e.format()}" for e in errors)
        )
    return analyzer
