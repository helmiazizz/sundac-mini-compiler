"""
setup.py
=========
Alternatif instalasi ringan: `pip install -e .` bakal masang paréntah
`sundac` salaku command-line tool (teu peryogi PyInstaller).

Pikeun installer mandiri (executable .exe / binary tanpa peryogi Python
kainstal), pake build_installer.sh (PyInstaller) -- tingali README.md.
"""

from setuptools import setup

setup(
    name="sundac",
    version="1.0.0",
    description="SUNDAC -- Kompiler Mini Basa Sunda (Lexer, Parser, AST, "
                 "Semantic Analysis, Code Optimization, Code Generation)",
    package_dir={"": "src"},
    py_modules=[
        "main", "lexer", "parser", "ast_nodes", "ast_builder",
        "semantic", "optimizer", "codegen", "errors",
    ],
    entry_points={
        "console_scripts": [
            "sundac=main:main",
        ],
    },
    python_requires=">=3.8",
)
