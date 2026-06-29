"""
codegen.py
===========
Tahap 6: CODE GENERATION (PEMBANGKITAN KODE)

Strategi: TRANSPILASI -- AST (anu geus dioptimasi) ditarjamahkeun jadi
kode sumber Python nu satara (equivalent). Sakur kecap konci Basa Sunda
(SIMPEN, UPAMA, SALILA, jst.) jeung fungsi bawaan (tembongkeun, asupkeun,
jst.) dipetakeun balik kana sintaksis & fungsi Python aslina, nuturkeun
"tabel pemetaan" dina lexer.py (KEYWORDS & BUILTIN_FUNCTIONS).

Kode Python hasil generate ieu nu satuluyna dieksekusi langsung ku
Python interpreter, atawa dibungkus jadi hiji executable mandiri
(installer) ku PyInstaller -- tingali build_installer.py.
"""

from ast_nodes import (
    Program, Literal, Identifier, BinOp, UnaryOp, ArrayLiteral, Index, Call,
)
from lexer import BUILTIN_FUNCTIONS

BIN_OP_MAP = {
    "PLUS": "+", "MINUS": "-", "KALI": "*", "BAGI": "/", "MODULO": "%",
    "EQ": "==", "NEQ": "!=", "LT": "<", "GT": ">", "LTE": "<=", "GTE": ">=",
    "JEUNG": "and", "ATAWA": "or",
}
UNARY_OP_MAP = {"MINUS": "-", "HENTEU": "not ", "NOT_SYM": "not "}


class CodeGenerator:
    def __init__(self):
        self.lines = []
        self.indent = 0

    def _emit(self, text=""):
        self.lines.append(("    " * self.indent) + text if text else "")

    # -- entry point --------------------------------------------------------
    def generate(self, program: Program) -> str:
        self.lines = []
        self._emit("# " + "=" * 68)
        self._emit("# Kode Python ieu di-generate otomatis ku Kompiler SUNDAC")
        self._emit("# tina kode sumber Basa Sunda (.sun) -- ulah diédit langsung.")
        self._emit("# " + "=" * 68)
        self._emit()
        if not program.statements:
            self._emit("pass")
        for stmt in program.statements:
            self.gen_stmt(stmt)
        return "\n".join(self.lines) + "\n"

    # -- statement ----------------------------------------------------------
    def gen_stmt(self, stmt):
        method = getattr(self, f"gen_{type(stmt).__name__}")
        method(stmt)

    def _gen_body(self, statements):
        if not statements:
            self._emit("pass")
            return
        for s in statements:
            self.gen_stmt(s)

    def gen_VarDecl(self, node):
        self._emit(f"{node.name} = {self.gen_expr(node.expr)}")

    def gen_Assign(self, node):
        self._emit(f"{node.name} = {self.gen_expr(node.expr)}")

    def gen_IndexAssign(self, node):
        self._emit(f"{self.gen_expr(node.obj)}[{self.gen_expr(node.index)}] = {self.gen_expr(node.value)}")

    def gen_If(self, node):
        self._emit(f"if {self.gen_expr(node.cond)}:")
        self.indent += 1
        self._gen_body(node.then_block.statements)
        self.indent -= 1
        for cond, block in node.elif_clauses:
            self._emit(f"elif {self.gen_expr(cond)}:")
            self.indent += 1
            self._gen_body(block.statements)
            self.indent -= 1
        if node.else_block is not None:
            self._emit("else:")
            self.indent += 1
            self._gen_body(node.else_block.statements)
            self.indent -= 1

    def gen_While(self, node):
        self._emit(f"while {self.gen_expr(node.cond)}:")
        self.indent += 1
        self._gen_body(node.body.statements)
        self.indent -= 1

    def gen_For(self, node):
        self._emit(f"for {node.var_name} in {self.gen_expr(node.iterable)}:")
        self.indent += 1
        self._gen_body(node.body.statements)
        self.indent -= 1

    def gen_FuncDecl(self, node):
        params = ", ".join(node.params)
        self._emit(f"def {node.name}({params}):")
        self.indent += 1
        self._gen_body(node.body.statements)
        self.indent -= 1
        self._emit()

    def gen_Return(self, node):
        self._emit(f"return {self.gen_expr(node.expr)}" if node.expr is not None else "return")

    def gen_Break(self, node):
        self._emit("break")

    def gen_Continue(self, node):
        self._emit("continue")

    def gen_Block(self, node):
        self._gen_body(node.statements)

    def gen_ExprStmt(self, node):
        self._emit(self.gen_expr(node.expr))

    # -- expression -> teks kode Python --------------------------------------
    def gen_expr(self, node):
        if isinstance(node, Literal):
            return self._gen_literal(node.value)
        if isinstance(node, Identifier):
            return node.name
        if isinstance(node, BinOp):
            op = BIN_OP_MAP[node.op]
            return f"({self.gen_expr(node.left)} {op} {self.gen_expr(node.right)})"
        if isinstance(node, UnaryOp):
            op = UNARY_OP_MAP[node.op]
            return f"({op}{self.gen_expr(node.operand)})"
        if isinstance(node, ArrayLiteral):
            items = ", ".join(self.gen_expr(e) for e in node.elements)
            return f"[{items}]"
        if isinstance(node, Index):
            return f"{self.gen_expr(node.obj)}[{self.gen_expr(node.index)}]"
        if isinstance(node, Call):
            callee_src = self._gen_callee(node.callee)
            args = ", ".join(self.gen_expr(a) for a in node.args)
            return f"{callee_src}({args})"
        raise ValueError(f"Code Generator: ekspresi teu dikenal: {type(node).__name__}")

    @staticmethod
    def _gen_callee(callee):
        if isinstance(callee, Identifier) and callee.name in BUILTIN_FUNCTIONS:
            return BUILTIN_FUNCTIONS[callee.name]
        if isinstance(callee, Identifier):
            return callee.name
        raise ValueError("Code Generator: pemanggilan fungsi nu kompleks teu didukung")

    @staticmethod
    def _gen_literal(value):
        if value is None:
            return "None"
        if value is True:
            return "True"
        if value is False:
            return "False"
        return repr(value)


def generate_code(program: Program) -> str:
    return CodeGenerator().generate(program)
