"""
lexer.py
=========
Tahap 1: ANALISIS LEKSIKAL (LEXER)

Tugasna: maca kode sumber (.sun) hiji-hiji karakter, terus dikelompokkeun
jadi runtuyan TOKEN nu boga harti (keyword, identifier, angka, string,
operator, jeung tanda baca). Kaluaran tina tahap ieu nyaeta daptar Token
nu bakal dipake ku tahap PARSER.
"""

from errors import LexerError


# ---------------------------------------------------------------------------
# 1. TABEL KEYWORD (KECAP KONCI) BASA SUNDA
# ---------------------------------------------------------------------------
# Ieu mangrupa "tabel simbol" pikeun kecap konci basa.
# Sakur kecap di sabeulah kenca bakal dikenal salaku TOKEN husus,
# lain salaku ngaran variabel (IDENTIFIER) biasa.

KEYWORDS = {
    "SIMPEN":     "SIMPEN",      # deklarasi variabel      (var/let)
    "UPAMA":      "UPAMA",       # percabangan             (if)
    "SABALIKNA":  "SABALIKNA",   # lamun teu kitu           (else)
    "SALILA":     "SALILA",      # perulangan kondisi      (while)
    "PIKEUN":     "PIKEUN",      # perulangan runtuyan     (for)
    "DINA":       "DINA",        # patali jeung PIKEUN     (in)
    "PANCEN":     "PANCEN",      # deklarasi fungsi        (function/def)
    "BALIKKEUN":  "BALIKKEUN",   # balikkeun nilai         (return)
    "EUREUN":     "EUREUN",      # eureun ti perulangan    (break)
    "TULUYKEUN":  "TULUYKEUN",   # terus ka iterasi saterus (continue)
    "BENER":      "BENER",       # nilai logika leres      (true)
    "SALAH":      "SALAH",       # nilai logika lepat      (false)
    "KOSONG":     "KOSONG",      # nilai kosong            (null/none)
    "JEUNG":      "JEUNG",       # logika AND              (and)
    "ATAWA":      "ATAWA",       # logika OR               (or)
    "HENTEU":     "HENTEU",      # logika NOT              (not)
}

# Fungsi bawaan (built-in) -- dikenal salaku IDENTIFIER biasa ku lexer,
# tapi dipetakeun ka fungsi Python aslina dina tahap CODE GENERATION.
BUILTIN_FUNCTIONS = {
    "tembongkeun":  "print",
    "asupkeun":     "input",
    "panjangna":    "len",
    "wilanganna":   "int",
    "pecahanna":    "float",
    "kecapna":      "str",
    "wengkuan":     "range",
    "rupana":       "type",
    "jumlahkeun":   "sum",
    "pangluhurna":  "max",
    "panghandapna": "min",
}


class Token:
    __slots__ = ("type", "value", "line", "col")

    def __init__(self, type_, value, line, col):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, baris={self.line}, kolom={self.col})"


SINGLE_CHAR_TOKENS = {
    "+": "PLUS", "-": "MINUS", "*": "KALI", "/": "BAGI", "%": "MODULO",
    "(": "LPAREN", ")": "RPAREN", "{": "LBRACE", "}": "RBRACE",
    "[": "LBRACKET", "]": "RBRACKET",
    ",": "COMMA", ";": "SEMI", ".": "DOT",
}


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens = []

    # -- util -----------------------------------------------------------
    def _peek(self, offset=0):
        i = self.pos + offset
        if i < len(self.source):
            return self.source[i]
        return "\0"

    def _advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _add(self, type_, value, line, col):
        self.tokens.append(Token(type_, value, line, col))

    # -- entry point ------------------------------------------------------
    def tokenize(self):
        while self.pos < len(self.source):
            ch = self._peek()

            if ch in " \t\r\n":
                self._advance()
                continue

            if ch == "/" and self._peek(1) == "/":
                while self.pos < len(self.source) and self._peek() != "\n":
                    self._advance()
                continue

            if ch == "/" and self._peek(1) == "*":
                start_line = self.line
                self._advance(); self._advance()
                while not (self._peek() == "*" and self._peek(1) == "/"):
                    if self.pos >= len(self.source):
                        raise LexerError("Komentar /* ... */ teu ditutup", start_line)
                    self._advance()
                self._advance(); self._advance()
                continue

            if ch.isdigit():
                self._read_number()
                continue

            if ch == '"':
                self._read_string()
                continue

            if ch.isalpha() or ch == "_":
                self._read_identifier()
                continue

            self._read_operator()

        self._add("EOF", None, self.line, self.col)
        return self.tokens

    # -- token readers ----------------------------------------------------
    def _read_number(self):
        line, col = self.line, self.col
        start = self.pos
        is_float = False
        while self._peek().isdigit():
            self._advance()
        if self._peek() == "." and self._peek(1).isdigit():
            is_float = True
            self._advance()
            while self._peek().isdigit():
                self._advance()
        text = self.source[start:self.pos]
        value = float(text) if is_float else int(text)
        self._add("FLOAT" if is_float else "INT", value, line, col)

    def _read_string(self):
        line, col = self.line, self.col
        self._advance()  # buka petik "
        chars = []
        while self._peek() != '"':
            if self.pos >= len(self.source):
                raise LexerError("String teu ditutup ku tanda petik (\")", line, col)
            ch = self._advance()
            if ch == "\\":
                esc = self._advance()
                mapping = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
                chars.append(mapping.get(esc, esc))
            else:
                chars.append(ch)
        self._advance()  # tutup petik "
        self._add("STRING", "".join(chars), line, col)

    def _read_identifier(self):
        line, col = self.line, self.col
        start = self.pos
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()
        text = self.source[start:self.pos]
        upper = text.upper()
        if upper in KEYWORDS:
            self._add(KEYWORDS[upper], text, line, col)
        else:
            self._add("IDENTIFIER", text, line, col)

    def _read_operator(self):
        line, col = self.line, self.col
        two = self._peek() + self._peek(1)
        two_char_ops = {
            "==": "EQ", "!=": "NEQ", "<=": "LTE", ">=": "GTE",
        }
        if two in two_char_ops:
            self._advance(); self._advance()
            self._add(two_char_ops[two], two, line, col)
            return

        ch = self._peek()
        if ch == "=":
            self._advance(); self._add("ASSIGN", "=", line, col); return
        if ch == "<":
            self._advance(); self._add("LT", "<", line, col); return
        if ch == ">":
            self._advance(); self._add("GT", ">", line, col); return
        if ch == "!":
            self._advance(); self._add("NOT_SYM", "!", line, col); return

        if ch in SINGLE_CHAR_TOKENS:
            self._advance()
            self._add(SINGLE_CHAR_TOKENS[ch], ch, line, col)
            return

        raise LexerError(f"Karakter teu dikenal: {ch!r}", line, col)


def tokenize_source(source: str):
    return Lexer(source).tokenize()
