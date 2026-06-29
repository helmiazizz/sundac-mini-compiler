"""
main.py
========
Titik mimiti (entry point) CLI pikeun SUNDAC -- Kompiler Mini Basa Sunda.

Ngahijikeun sakabéh tahapan:
    Source (.sun) -> LEXER -> PARSER (Parse Tree) -> AST BUILDER (AST)
    -> SEMANTIC ANALYSIS -> CODE OPTIMIZATION -> CODE GENERATION (.py)

Pamakean:
    sundac run program.sun                 # kompilasi + langsung jalankeun
    sundac compile program.sun -o out.py   # kompilasi -> file .py wungkul
    sundac run program.sun --tokens --ast --pycode   # tembongkeun unggal tahap
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lexer import tokenize_source
from parser import parse_tokens
from ast_builder import build_ast
from ast_nodes import pretty_print
from semantic import analyze_program
from optimizer import optimize_program
from codegen import generate_code
from errors import SundacError

BANNER = r"""
   ____  _   _ _   _ ____    _    ____
  / ___|| | | | \ | |  _ \  / \  / ___|
  \___ \| | | |  \| | | | |/ _ \| |
   ___) | |_| | |\  | |_| / ___ \ |___
  |____/ \___/|_| \_|____/_/   \_\____|

  Kompiler Mini Basa Sunda  |  UAS Kompilasi
"""


def compile_source(source, *, show_tokens=False, show_parsetree=False,
                    show_ast=False, show_optimized_ast=False,
                    show_pycode=False, no_optimize=False, quiet=False):
    """Ngajalankeun sakabéh tahap kompilasi, balikkeun (kode_python, stats)."""

    # TAHAP 1: LEXER ------------------------------------------------------
    tokens = tokenize_source(source)
    if show_tokens:
        print("=== TAHAP 1: LEXER (TOKEN) ===")
        for t in tokens:
            print(f"  {t}")
        print()

    # TAHAP 2: PARSER -> PARSE TREE ----------------------------------------
    parse_tree = parse_tokens(tokens)
    if show_parsetree:
        print("=== TAHAP 2: PARSER -> PARSE TREE (CST) ===")
        print(parse_tree.pretty())
        print()

    # TAHAP 3: AST ----------------------------------------------------------
    ast = build_ast(parse_tree)
    if show_ast:
        print("=== TAHAP 3: AST (sateuacan optimasi) ===")
        print(pretty_print(ast))
        print()

    # TAHAP 4: SEMANTIC ANALYSIS --------------------------------------------
    analyze_program(ast)
    if not quiet:
        print("[OK] Semantic Analysis: euweuh kasalahan.")

    # TAHAP 5: CODE OPTIMIZATION ---------------------------------------------
    if no_optimize:
        optimized_ast, stats = ast, {"constant_folded": 0, "dead_code_removed": 0}
    else:
        optimized_ast, stats = optimize_program(ast)
    if not quiet:
        print(f"[OK] Code Optimization: {stats['constant_folded']} ekspresi dilipet "
              f"(constant folding), {stats['dead_code_removed']} statement dibuang "
              f"(dead code elimination).")
    if show_optimized_ast:
        print("\n=== TAHAP 5: AST (sanggeus optimasi) ===")
        print(pretty_print(optimized_ast))
        print()

    # TAHAP 6: CODE GENERATION ------------------------------------------------
    py_code = generate_code(optimized_ast)
    if not quiet:
        print("[OK] Code Generation: kode Python geus dihasilkeun.\n")
    if show_pycode:
        print("=== TAHAP 6: KODE PYTHON HASIL GENERATE ===")
        print(py_code)

    return py_code, stats


def build_arg_parser():
    p = argparse.ArgumentParser(
        prog="sundac",
        description="SUNDAC -- Kompiler Mini Basa Sunda (Lexer, Parser, AST, "
                     "Semantic Analysis, Code Optimization, Code Generation)",
    )
    sub = p.add_subparsers(dest="command", required=True)

    def add_common(sp):
        sp.add_argument("file", help="File sumber Basa Sunda (.sun)")
        sp.add_argument("--tokens", action="store_true", help="Tembongkeun hasil Lexer (token)")
        sp.add_argument("--parsetree", action="store_true", help="Tembongkeun Parse Tree (CST)")
        sp.add_argument("--ast", action="store_true", help="Tembongkeun AST sateuacan optimasi")
        sp.add_argument("--optimized-ast", action="store_true", help="Tembongkeun AST sanggeus optimasi")
        sp.add_argument("--pycode", action="store_true", help="Tembongkeun kode Python hasil generate")
        sp.add_argument("--no-optimize", action="store_true", help="Lompatan tahap Code Optimization")
        sp.add_argument("-q", "--quiet", action="store_true", help="Tong nembongkeun pesen status tahap")

    p_run = sub.add_parser("run", help="Kompilasi tur langsung jalankeun program")
    add_common(p_run)

    p_compile = sub.add_parser("compile", help="Kompilasi jadi file .py wungkul (teu dijalankeun)")
    add_common(p_compile)
    p_compile.add_argument("-o", "--output", help="Ngaran file .py kaluaran (default: <ngaran>.py)")

    return p


def main(argv=None):
    args = build_arg_parser().parse_args(argv)

    if not os.path.isfile(args.file):
        print(f"Error: file '{args.file}' teu kapanggih.", file=sys.stderr)
        return 1

    with open(args.file, "r", encoding="utf-8") as f:
        source = f.read()

    if not args.quiet:
        print(BANNER)
        print(f"Ngompilasi: {args.file}\n")

    try:
        py_code, _ = compile_source(
            source,
            show_tokens=args.tokens,
            show_parsetree=args.parsetree,
            show_ast=args.ast,
            show_optimized_ast=args.optimized_ast,
            show_pycode=args.pycode,
            no_optimize=args.no_optimize,
            quiet=args.quiet,
        )
    except SundacError as e:
        print("\n*** KOMPILASI GAGAL ***", file=sys.stderr)
        print(str(e), file=sys.stderr)
        return 1

    if args.command == "compile":
        out_path = args.output or (os.path.splitext(args.file)[0] + ".py")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(py_code)
        print(f"Suksés! Kode Python disimpen di: {out_path}")
        return 0

    # command == "run"
    if not args.quiet:
        print("--- Kaluaran Program ---\n")
    exec_globals = {"__name__": "__sundac_program__"}
    try:
        exec(compile(py_code, args.file, "exec"), exec_globals)
    except Exception as e:
        print(f"\n*** ERROR WAKTU NGAJALANKEUN PROGRAM ***\n{type(e).__name__}: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
