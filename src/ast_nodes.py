"""
ast_nodes.py
=============
Tahap 3: AST (ABSTRACT SYNTAX TREE)

Béda jeung Parse Tree (CST) anu nuturkeun grammar 1:1 (loba simpul
"perantara" kayaning term/factor/group), AST ngan nyimpen INTI MAKNA
tina program: naon statement-na, naon ekspresi-na -- tanpa simpul
perantara nu teu perlu. AST ieu nu bakal dipake ku tahap saterusna:
Semantic Analysis, Optimizer, jeung Code Generator.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Tuple


class ASTNode:
    """Tanda (marker) dasar pikeun sadaya simpul AST."""


# ---------------------------------------------------------------------------
# STATEMENT
# ---------------------------------------------------------------------------

@dataclass
class Program(ASTNode):
    statements: List[Any]
    line: int = 0


@dataclass
class VarDecl(ASTNode):
    """SIMPEN nama = ekspresi ;"""
    name: str
    expr: Any
    line: int = 0


@dataclass
class Assign(ASTNode):
    """nama = ekspresi ;"""
    name: str
    expr: Any
    line: int = 0


@dataclass
class IndexAssign(ASTNode):
    """obj[indeks] = ekspresi ;"""
    obj: Any
    index: Any
    value: Any
    line: int = 0


@dataclass
class If(ASTNode):
    cond: Any
    then_block: Any
    elif_clauses: List[Tuple[Any, Any]]
    else_block: Optional[Any]
    line: int = 0


@dataclass
class While(ASTNode):
    cond: Any
    body: Any
    line: int = 0


@dataclass
class For(ASTNode):
    var_name: str
    iterable: Any
    body: Any
    line: int = 0


@dataclass
class FuncDecl(ASTNode):
    name: str
    params: List[str]
    body: Any
    line: int = 0


@dataclass
class Return(ASTNode):
    expr: Optional[Any]
    line: int = 0


@dataclass
class Break(ASTNode):
    line: int = 0


@dataclass
class Continue(ASTNode):
    line: int = 0


@dataclass
class Block(ASTNode):
    statements: List[Any]
    line: int = 0


@dataclass
class ExprStmt(ASTNode):
    expr: Any
    line: int = 0


# ---------------------------------------------------------------------------
# EXPRESSION
# ---------------------------------------------------------------------------

@dataclass
class BinOp(ASTNode):
    op: str          # cth: "PLUS", "KALI", "EQ", "JEUNG", dst.
    left: Any
    right: Any
    line: int = 0


@dataclass
class UnaryOp(ASTNode):
    op: str          # "MINUS" atawa "HENTEU"
    operand: Any
    line: int = 0


@dataclass
class Literal(ASTNode):
    value: Any       # int / float / str / bool / None
    line: int = 0


@dataclass
class Identifier(ASTNode):
    name: str
    line: int = 0


@dataclass
class Call(ASTNode):
    callee: Any
    args: List[Any]
    line: int = 0


@dataclass
class Index(ASTNode):
    obj: Any
    index: Any
    line: int = 0


@dataclass
class ArrayLiteral(ASTNode):
    elements: List[Any]
    line: int = 0


def pretty_print(node, depth=0):
    """Cetak AST kalayan rapih (indented), kanggo debugging / demo."""
    pad = "  " * depth
    if isinstance(node, list):
        return "\n".join(pretty_print(n, depth) for n in node)
    if not isinstance(node, ASTNode):
        return f"{pad}{node!r}"

    cls = node.__class__.__name__
    lines = [f"{pad}{cls}" + (f"  (baris {node.line})" if getattr(node, 'line', 0) else "")]
    for f in node.__dataclass_fields__:
        if f == "line":
            continue
        val = getattr(node, f)
        if isinstance(val, ASTNode):
            lines.append(f"{pad}  {f}:")
            lines.append(pretty_print(val, depth + 2))
        elif isinstance(val, list):
            lines.append(f"{pad}  {f}: [{len(val)}]")
            for item in val:
                if isinstance(item, tuple):
                    for sub in item:
                        lines.append(pretty_print(sub, depth + 2))
                else:
                    lines.append(pretty_print(item, depth + 2))
        else:
            lines.append(f"{pad}  {f}: {val!r}")
    return "\n".join(lines)
