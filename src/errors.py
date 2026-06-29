"""
errors.py
Kelas-kelas kasalahan (exception) pikeun unggal tahapan Kompiler SUNDAC.
"""


class SundacError(Exception):
    """Kelas dasar pikeun sadaya kasalahan kompiler SUNDAC."""

    def __init__(self, message, line=None, col=None):
        self.message = message
        self.line = line
        self.col = col
        super().__init__(self.format())

    def format(self):
        loc = ""
        if self.line is not None:
            loc = f" [baris {self.line}"
            if self.col is not None:
                loc += f", kolom {self.col}"
            loc += "]"
        tag = self.__class__.__name__.replace("Error", "")
        return f"{tag}{loc}: {self.message}"

    def __str__(self):
        return self.format()


class LexerError(SundacError):
    """Kasalahan dina tahap Analisis Leksikal (Lexer)."""


class ParserError(SundacError):
    """Kasalahan dina tahap Analisis Sintaksis (Parser -> Parse Tree)."""


class SemanticError(SundacError):
    """Kasalahan dina tahap Analisis Semantik."""
