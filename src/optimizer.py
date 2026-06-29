"""
optimizer.py
=============
Tahap 5: CODE OPTIMIZATION (OPTIMASI KODE)

Dilaksanakeun di luhureun AST (sanggeus Semantic Analysis lulus, sateuacan
Code Generation). Dua téhnik optimasi nu dipake:

  1. CONSTANT FOLDING
     Ekspresi nu kadua operand-na konstan dihirung langsung waktu kompilasi.
     Conto:  2 + 3 * 4   ->   14   (teu kudu dihirung deui unggal program dijalankeun)

  2. DEAD CODE ELIMINATION
     - Statement sanggeus BALIKKEUN/EUREUN/TULUYKEUN dina hiji blok nu sarua
       moal kungsi kahontal, jadi dibuang.
     - UPAMA (BENER) {...}  disederhanakeun jadi eusi blok-na wungkul.
     - UPAMA (SALAH) {...} (tanpa elif) dibuang, ganti ku blok SABALIKNA
       (lamun aya), atawa dibuang lengkep lamun teu aya SABALIKNA.
     - SALILA (SALAH) {...} dibuang lengkep (moal kungsi jalan).
"""

from ast_nodes import (
    Program, VarDecl, Assign, IndexAssign, If, While, For, FuncDecl,
    Return, Break, Continue, Block, ExprStmt,
    BinOp, UnaryOp, Literal, Identifier, Call, Index, ArrayLiteral,
)

_SKIP = object()  # tanda yen ekspresi teu bisa (atawa teu aman) dilipet (fold)


class Optimizer:
    def __init__(self):
        self.stats = {"constant_folded": 0, "dead_code_removed": 0}

    # -- API umum -----------------------------------------------------------
    def optimize(self, program: Program) -> Program:
        stmts = self._optimize_block_stmts(program.statements)
        return Program(stmts, line=program.line)

    # -- statement --------------------------------------------------------
    def _optimize_block_stmts(self, statements):
        result = []
        terminated = False
        for stmt in statements:
            if terminated:
                self.stats["dead_code_removed"] += 1
                continue
            new_stmt = self.optimize_stmt(stmt)
            if new_stmt is None:
                continue
            result.append(new_stmt)
            if isinstance(new_stmt, (Return, Break, Continue)):
                terminated = True
        return result

    def optimize_stmt(self, stmt):
        method = getattr(self, f"opt_{type(stmt).__name__}", None)
        return method(stmt) if method else stmt

    def opt_VarDecl(self, node):
        return VarDecl(node.name, self.optimize_expr(node.expr), line=node.line)

    def opt_Assign(self, node):
        return Assign(node.name, self.optimize_expr(node.expr), line=node.line)

    def opt_IndexAssign(self, node):
        return IndexAssign(
            self.optimize_expr(node.obj), self.optimize_expr(node.index),
            self.optimize_expr(node.value), line=node.line)

    def opt_If(self, node):
        cond = self.optimize_expr(node.cond)

        if isinstance(cond, Literal):
            if cond.value:
                self.stats["dead_code_removed"] += 1 + len(node.elif_clauses) + (1 if node.else_block else 0)
                return Block(self._optimize_block_stmts(node.then_block.statements), line=node.line)
            if not node.elif_clauses:
                self.stats["dead_code_removed"] += 1
                if node.else_block:
                    return Block(self._optimize_block_stmts(node.else_block.statements), line=node.line)
                return None

        then_block = Block(self._optimize_block_stmts(node.then_block.statements), line=node.then_block.line)
        elif_clauses = [
            (self.optimize_expr(ec), Block(self._optimize_block_stmts(eb.statements), line=eb.line))
            for ec, eb in node.elif_clauses
        ]
        else_block = (
            Block(self._optimize_block_stmts(node.else_block.statements), line=node.else_block.line)
            if node.else_block else None
        )
        return If(cond, then_block, elif_clauses, else_block, line=node.line)

    def opt_While(self, node):
        cond = self.optimize_expr(node.cond)
        if isinstance(cond, Literal) and not cond.value:
            self.stats["dead_code_removed"] += 1
            return None
        body = Block(self._optimize_block_stmts(node.body.statements), line=node.body.line)
        return While(cond, body, line=node.line)

    def opt_For(self, node):
        iterable = self.optimize_expr(node.iterable)
        body = Block(self._optimize_block_stmts(node.body.statements), line=node.body.line)
        return For(node.var_name, iterable, body, line=node.line)

    def opt_FuncDecl(self, node):
        body = Block(self._optimize_block_stmts(node.body.statements), line=node.body.line)
        return FuncDecl(node.name, node.params, body, line=node.line)

    def opt_Return(self, node):
        expr = self.optimize_expr(node.expr) if node.expr is not None else None
        return Return(expr, line=node.line)

    def opt_Break(self, node):
        return node

    def opt_Continue(self, node):
        return node

    def opt_Block(self, node):
        return Block(self._optimize_block_stmts(node.statements), line=node.line)

    def opt_ExprStmt(self, node):
        return ExprStmt(self.optimize_expr(node.expr), line=node.line)

    # -- expression: CONSTANT FOLDING --------------------------------------
    def optimize_expr(self, node):
        if isinstance(node, (Literal, Identifier)):
            return node

        if isinstance(node, ArrayLiteral):
            return ArrayLiteral([self.optimize_expr(e) for e in node.elements], line=node.line)

        if isinstance(node, Index):
            return Index(self.optimize_expr(node.obj), self.optimize_expr(node.index), line=node.line)

        if isinstance(node, Call):
            return Call(node.callee, [self.optimize_expr(a) for a in node.args], line=node.line)

        if isinstance(node, UnaryOp):
            operand = self.optimize_expr(node.operand)
            if isinstance(operand, Literal):
                val = self._fold_unary(node.op, operand.value)
                if val is not _SKIP:
                    self.stats["constant_folded"] += 1
                    return Literal(val, line=node.line)
            return UnaryOp(node.op, operand, line=node.line)

        if isinstance(node, BinOp):
            left = self.optimize_expr(node.left)
            right = self.optimize_expr(node.right)
            if isinstance(left, Literal) and isinstance(right, Literal):
                val = self._fold_binary(node.op, left.value, right.value)
                if val is not _SKIP:
                    self.stats["constant_folded"] += 1
                    return Literal(val, line=node.line)
            return BinOp(node.op, left, right, line=node.line)

        return node

    @staticmethod
    def _fold_binary(op, a, b):
        try:
            if op == "PLUS":
                return a + b
            if op == "MINUS":
                return a - b
            if op == "KALI":
                return a * b
            if op == "BAGI":
                return _SKIP if b == 0 else a / b
            if op == "MODULO":
                return _SKIP if b == 0 else a % b
            if op == "EQ":
                return a == b
            if op == "NEQ":
                return a != b
            if op == "LT":
                return a < b
            if op == "GT":
                return a > b
            if op == "LTE":
                return a <= b
            if op == "GTE":
                return a >= b
            if op == "JEUNG":
                return bool(a) and bool(b)
            if op == "ATAWA":
                return bool(a) or bool(b)
        except TypeError:
            return _SKIP
        return _SKIP

    @staticmethod
    def _fold_unary(op, a):
        try:
            if op == "MINUS":
                return -a
            if op in ("HENTEU", "NOT_SYM"):
                return not bool(a)
        except TypeError:
            return _SKIP
        return _SKIP


def optimize_program(program: Program):
    opt = Optimizer()
    new_program = opt.optimize(program)
    return new_program, opt.stats
