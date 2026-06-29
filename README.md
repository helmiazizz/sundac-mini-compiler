# SUNDAC — Kompiler Mini Basa Sunda

> Tugas UAS Mata Kuliah Kompilasi / Teori Bahasa & Otomata
> Mini Compiler nganggo Python, kalayan kecap konci jeung fungsi bawaan
> dialihbasakeun kana **Basa Sunda**.

Ekstensi file sumber: **`.sun`**
Paréntah CLI: **`sundac`**

---

## 1. Latar Belakang & Tujuan

SUNDAC nyaeta hiji *mini compiler* nu dibangun lengkep ti nol nganggo
Python, kalayan ngalaksanakeun genep tahapan kompilasi klasik:

```
Kode Sumber (.sun)
      │
      ▼
 ① LEXER  ──────────► runtuyan TOKEN
      │
      ▼
 ② PARSER ──────────► PARSE TREE (Concrete Syntax Tree)
      │
      ▼
 ③ AST BUILDER ─────► AST (Abstract Syntax Tree)
      │
      ▼
 ④ SEMANTIC ANALYSIS ► Tabel Simbol + validasi (atawa error)
      │
      ▼
 ⑤ CODE OPTIMIZATION ► AST nu geus disederhanakeun
      │
      ▼
 ⑥ CODE GENERATION ──► Kode Python (.py) ──► [PyInstaller] ──► Installer/Executable
```

Strategi Code Generation nu dipake nyaeta **transpilasi**: AST hasil
optimasi ditarjamahkeun jadi kode sumber Python nu satara, sabab
kompiler ieu sorangan ditulis dina Python. Kode Python hasilna bisa
langsung dieksekusi, atawa dibungkus jadi hiji *executable* mandiri
(installer) ku PyInstaller, sahingga bisa dijalankeun di komputer lian
sanaos teu kainstal Python.

---

## 2. Desain Basa

| Aspek | Kaputusan Desain |
|---|---|
| Paradigma | Imperatif, prosedural (kawas Python/JavaScript basajan) |
| Tipe data | Dinamis (teu peryogi deklarasi tipe eksplisit) — `wilangan` (int/float), `kecap` (string), boolean (`BENER`/`SALAH`), `KOSONG` (null), Larik/Array |
| Wewengkon (scope) | Function-scoped (saluyu jeung target generate-na, nyaeta Python) |
| Blok kode | Ditandaan ku `{ }` (gaya C/Java, sangkan parsing leuwih basajan tur jelas) |
| Statement | Ditutup ku `;` |
| Komentar | `// komentar sabaris` jeung `/* komentar lobaan baris */` |
| Operator | Dianggo simbol matematika baku (`+ - * / % == != < > <= >=`) sabab éta geus universal; nu diterjemahkeun kana Basa Sunda nyaeta **kecap konci** jeung **fungsi bawaan** |
| Case-sensitivity keyword | Teu sénsitif huruf gede/leutik (`upama`, `Upama`, `UPAMA` sarua) |

---

## 3. Tabel Kecap Konci (Keyword) — Basa Sunda

Ieu mangrupa "tabel simbol" pikeun kecap konci basa (didefinisikeun
dina `src/lexer.py`, dict `KEYWORDS`):

| Kecap Sunda | Padanan | Fungsi |
|---|---|---|
| `SIMPEN` | `var` / `let` | Deklarasi variabel |
| `UPAMA` | `if` | Percabangan |
| `SABALIKNA` | `else` | Cabang lamun teu kitu (bisa dikombinasikeun: `SABALIKNA UPAMA` = `else if`) |
| `SALILA` | `while` | Perulangan kondisi |
| `PIKEUN ... DINA` | `for ... in` | Perulangan runtuyan (larik / `wengkuan`) |
| `PANCEN` | `function` / `def` | Deklarasi fungsi |
| `BALIKKEUN` | `return` | Balikkeun nilai ti pancen |
| `EUREUN` | `break` | Eureun ti perulangan |
| `TULUYKEUN` | `continue` | Lanjut ka iterasi saterusna |
| `BENER` | `true` | Nilai logika leres |
| `SALAH` | `false` | Nilai logika lepat |
| `KOSONG` | `null` / `None` | Nilai kosong |
| `JEUNG` | `and` | Logika AND |
| `ATAWA` | `or` | Logika OR |
| `HENTEU` | `not` | Logika NOT |

## 4. Tabel Fungsi Bawaan (Built-in Functions)

Didefinisikeun dina `src/lexer.py`, dict `BUILTIN_FUNCTIONS`, dipetakeun
balik ka fungsi Python aslina dina tahap Code Generation:

| Fungsi Sunda | Fungsi Python | Kagunaan |
|---|---|---|
| `tembongkeun(...)` | `print(...)` | Nembongkeun/nyitak kaluaran |
| `asupkeun(...)` | `input(...)` | Maca asupan ti pamake |
| `panjangna(x)` | `len(x)` | Panjang larik/kecap |
| `wilanganna(x)` | `int(x)` | Ngarobah jadi wilangan bulat |
| `pecahanna(x)` | `float(x)` | Ngarobah jadi wilangan pecahan |
| `kecapna(x)` | `str(x)` | Ngarobah jadi kecap (string) |
| `wengkuan(...)` | `range(...)` | Runtuyan wilangan (pikeun `PIKEUN..DINA`) |
| `rupana(x)` | `type(x)` | Mariksa rupa/tipe nilai |
| `jumlahkeun(x)` | `sum(x)` | Jumlah sadaya unsur larik |
| `pangluhurna(x)` | `max(x)` | Nilai pangluhurna |
| `panghandapna(x)` | `min(x)` | Nilai panghandapna |

---

## 5. Grammar (EBNF)

```ebnf
program        ::= statement* EOF

statement       ::= var_decl | assign_stmt | index_assign_stmt
                   | if_stmt | while_stmt | for_stmt | func_decl
                   | return_stmt | break_stmt | continue_stmt
                   | block | expr_stmt

var_decl        ::= "SIMPEN" IDENT "=" expression ";"
assign_stmt     ::= IDENT "=" expression ";"
index_assign_stmt ::= IDENT "[" expression "]" "=" expression ";"

if_stmt         ::= "UPAMA" "(" expression ")" block
                     ( "SABALIKNA" "UPAMA" "(" expression ")" block )*
                     ( "SABALIKNA" block )?

while_stmt      ::= "SALILA" "(" expression ")" block
for_stmt        ::= "PIKEUN" IDENT "DINA" expression block

func_decl       ::= "PANCEN" IDENT "(" param_list? ")" block
param_list      ::= IDENT ( "," IDENT )*

return_stmt     ::= "BALIKKEUN" expression? ";"
break_stmt      ::= "EUREUN" ";"
continue_stmt   ::= "TULUYKEUN" ";"
block           ::= "{" statement* "}"
expr_stmt       ::= expression ";"

expression      ::= logic_or
logic_or        ::= logic_and ( "ATAWA" logic_and )*
logic_and       ::= equality ( "JEUNG" equality )*
equality        ::= comparison ( ("==" | "!=") comparison )*
comparison      ::= term ( ("<" | ">" | "<=" | ">=") term )*
term            ::= factor ( ("+" | "-") factor )*
factor          ::= unary ( ("*" | "/" | "%") unary )*
unary           ::= ( "HENTEU" | "-" ) unary | call
call            ::= primary ( "(" args? ")" | "[" expression "]" )*
args            ::= expression ( "," expression )*

primary         ::= INT | FLOAT | STRING | "BENER" | "SALAH" | "KOSONG"
                   | IDENT | "(" expression ")" | array_literal
array_literal   ::= "[" ( expression ( "," expression )* )? "]"
```

Catetan: precedence operator (ti nu pangrendahna nepi ka panggedéna)
nuturkeun urutan aturan: `ATAWA` < `JEUNG` < persamaan < perbandingan
< tambah/kurang < kali/bagi/modulo < unary — persis kawas basa
pemrograman umumna, ditangtukeun ku struktur grammar di luhur
("precedence climbing" dina recursive-descent parser).

---

## 6. Tabel Simbol (Symbol Table)

Tabel simbol diwangun sacara DINAMIS ku `src/semantic.py` (kelas
`Scope`) bari napel kana AST. Unggal *scope* (global atawa jero
pancen) boga tabel sorangan, sarta neangan ka *scope* karuhun
(parent) lamun ngaran teu kapanggih lokal (lexical scoping).

Conto eusi tabel simbol pikeun program ieu:

```sunda
SIMPEN x = 5;
PANCEN tambah(a, b) {
    BALIKKEUN a + b;
}
```

| Scope | Ngaran | Jenis (kind) | Info Tambahan |
|---|---|---|---|
| global | `x` | var | baris 1 |
| global | `tambah` | func | params=[a, b], baris 2 |
| tambah() | `a` | param | baris 2 |
| tambah() | `b` | param | baris 2 |

Validasi nu dilaksanakeun nganggo tabel simbol ieu:
- Variabel kudu aya dina tabel (dideklarasikeun) saméméh dipaké.
- Teu meunang `SIMPEN` ngaran nu sarua dua kali dina scope nu sarua.
- Jumlah argumen waktu manggil pancen kudu cocog jeung jumlah parameter.
- `BALIKKEUN` ngan sah lamun keur di jero scope pancen.
- `EUREUN` / `TULUYKEUN` ngan sah lamun keur di jero perulangan.

---

## 7. Arsitektur Kompiler (Penjelasan Tiap Tahap)

| # | Tahap | File | Input | Output |
|---|---|---|---|---|
| 1 | **Lexer** | `src/lexer.py` | Kode sumber (teks) | Daptar `Token` |
| 2 | **Parser** | `src/parser.py` | Daptar `Token` | `ParseTreeNode` (Parse Tree / CST) |
| 3 | **AST Builder** | `src/ast_builder.py` + `src/ast_nodes.py` | Parse Tree | AST (`Program`, `If`, `BinOp`, dst.) |
| 4 | **Semantic Analysis** | `src/semantic.py` | AST | Tabel Simbol + (raises error lamun teu valid) |
| 5 | **Code Optimization** | `src/optimizer.py` | AST | AST nu geus disederhanakeun |
| 6 | **Code Generation** | `src/codegen.py` | AST (optimal) | String kode Python |
| – | **Driver / CLI** | `src/main.py` | File `.sun` | Ngajalankeun/nyimpen hasil |
| – | **Installer Builder** | `build_installer.sh` | `src/main.py` | Executable mandiri (`sundac` / `sundac.exe`) |

### 7.1 Lexer (`lexer.py`)
Maca kode sumber hiji-hiji karakter, ngahasilkeun token: keyword
(dipetakeun ti dict `KEYWORDS`), `IDENTIFIER`, `INT`/`FLOAT`, `STRING`,
operator, jeung tanda baca. Komentar (`//` jeung `/* */`) dileungitkeun
dina tahap ieu. Unggal token nyimpen posisi (baris & kolom) pikeun
keperluan laporan error.

### 7.2 Parser → Parse Tree (`parser.py`)
Nganggo metode **Recursive Descent**, nuturkeun grammar EBNF di luhur.
Unggal aturan grammar (cth. `if_stmt`, `term`, `factor`) jadi hiji
fungsi (`_if_stmt()`, `_term()`, `_factor()`, dst.) nu ngahasilkeun
`ParseTreeNode`. Wangun tangkal ieu nuturkeun grammar 1:1 (loba simpul
"perantara" kawas `term`/`factor`/`group`), béda jeung AST nu leuwih
basajan.

### 7.3 AST (`ast_nodes.py`, `ast_builder.py`)
`ast_builder.py` "nyaring" Parse Tree jadi AST: simpul perantara
(`term`, `factor`, `group`, jrrd.) digabungkeun jadi `BinOp`/`UnaryOp`
nu langsung nyimpen operator-na, sarta `group` (tanda kurung) leungit
sabab geus kawakilan ku struktur tangkal-na sorangan. AST inilah anu
dipake ku tahap-tahap saterusna.

### 7.4 Semantic Analysis (`semantic.py`)
Napelan (traverse) AST bari ngabangun jeung meriksa Tabel Simbol
(tingali Bagian 6). Sadaya kasalahan dikumpulkeun heula (teu langsung
eureun dina kasalahan kahiji), sangkan sakabéh kasalahan bisa
dilaporkeun sakaligus ka pamake — kawas kompiler beneran.

### 7.5 Code Optimization (`optimizer.py`)
Dua téhnik anu diterapkeun di luhureun AST:
- **Constant Folding**: ekspresi konstan (cth. `2 + 3 * 4`) dihirung
  langsung wektu kompilasi jadi `14`, teu kudu dihirung deui unggal
  program dijalankeun.
- **Dead Code Elimination**: statement sanggeus `BALIKKEUN`/`EUREUN`/
  `TULUYKEUN` dina blok nu sarua dibuang (moal kungsi kahontal);
  `UPAMA (BENER) {...}` disederhanakeun jadi eusi blokna wungkul;
  `UPAMA (SALAH) {...}` (tanpa elif) diganti ku blok `SABALIKNA` (lamun
  aya) atawa dibuang lengkep; `SALILA (SALAH) {...}` dibuang lengkep.

Pamakean `--optimized-ast` dina CLI bisa nembongkeun bédana AST
saméméh jeung sanggeus optimasi (tingali `examples/04_demo_optimasi.sun`).

### 7.6 Code Generation (`codegen.py`)
AST (hasil optimasi) ditarjamahkeun (transpile) jadi kode sumber
Python nu satara. Kecap konci geus ilang (geus jadi struktur tangkal),
nu diterjemahkeun balik nyaeta **ngaran fungsi bawaan** (nganggo dict
`BUILTIN_FUNCTIONS`), contona `tembongkeun(...)` ➜ `print(...)`. Kode
Python hasilna bisa langsung dieksekusi (`sundac run`), disimpen jadi
`.py` (`sundac compile`), atawa dibungkus jadi **installer**.

---

## 8. Struktur Proyék

```
sundac/
├── src/
│   ├── lexer.py          # Tahap 1: Lexer
│   ├── parser.py         # Tahap 2: Parser -> Parse Tree
│   ├── ast_nodes.py       # Struktur data AST
│   ├── ast_builder.py     # Tahap 3: Parse Tree -> AST
│   ├── semantic.py        # Tahap 4: Semantic Analysis
│   ├── optimizer.py       # Tahap 5: Code Optimization
│   ├── codegen.py         # Tahap 6: Code Generation
│   ├── errors.py          # Kelas exception kompiler
│   └── main.py            # CLI driver (sundac run / compile)
├── examples/               # Conto program .sun
│   ├── 01_halo_dunya.sun
│   ├── 02_fungsi_prima.sun
│   ├── 03_larik.sun
│   ├── 04_demo_optimasi.sun
│   └── 05_contoh_error.sun
├── build/
│   └── dist/sundac         # Hasil build installer (PyInstaller)
├── docs/
│   └── video_script.md     # Naskah/outline video dokumentasi
├── demo.sh                 # Script demo otomatis (pikeun rékaman video)
├── build_installer.sh      # Skrip ngabangun installer
├── setup.py                # Alternatif instalasi via pip
├── requirements.txt
└── README.md                # Dokumén ieu
```

---

## 9. Instalasi & Cara Pakai

### A. Langsung jalankeun nganggo Python (paling gancang, kanggo development)

```bash
cd sundac
python3 src/main.py run examples/02_fungsi_prima.sun
```

Pilihan (flag) nu sayogi pikeun nembongkeun unggal tahap kompilasi:

```bash
python3 src/main.py run examples/01_halo_dunya.sun \
    --tokens --parsetree --ast --optimized-ast --pycode
```

| Flag | Nembongkeun |
|---|---|
| `--tokens` | Hasil Lexer (Tahap 1) |
| `--parsetree` | Parse Tree / CST (Tahap 2) |
| `--ast` | AST saméméh optimasi (Tahap 3) |
| `--optimized-ast` | AST sanggeus optimasi (Tahap 5) |
| `--pycode` | Kode Python hasil generate (Tahap 6) |
| `--no-optimize` | Lompatan tahap optimasi |
| `-q` / `--quiet` | Mode sepi (ngan kaluaran program) |

Ngompilasi jadi file `.py` wungkul (teu langsung dijalankeun):

```bash
python3 src/main.py compile examples/03_larik.sun -o hasil.py
python3 hasil.py        # kode hasilna kode Python murni, bisa dijalankeun di mana wae
```

### B. Instalasi via pip (alternatif ringan)

```bash
cd sundac
pip install -e .
sundac run examples/02_fungsi_prima.sun
```

### C. Naskah Presentasi (untuk rekaman video yang natural)

Untuk rekaman video yang terasa natural (Anda yang ngomong dan
mengetik sendiri, bukan sekadar baca "tekan ENTER"), pakai naskah di
`docs/video_script.md` — berisi panduan lengkap: file apa yang dibuka,
perintah apa yang diketik, dan apa yang sebaiknya diomongkan di tiap
bagian, ditarget ±20 menit total (aman di atas minimal 15 menit).

Untuk **latihan** dulu sebelum rekam asli (supaya hafal urutan
perintahnya), boleh pakai script otomatis -- bakal menjalankan
sakabéh tahap sacara runtut kalayan pause:

**Linux / macOS / Git Bash / WSL** (boga distro Linux nu aktif):
```bash
bash demo.sh
```

**Windows (PowerShell, paling gampang -- teu peryogi WSL/Git Bash):**
```powershell
.\demo.ps1
```
Lamun mucul pesen *"running scripts is disabled on this system"*,
jalankeun heula (sakali wae) di PowerShell:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy Bypass -Force
```

> **Troubleshooting**: lamun nyobaan `bash demo.sh` di Windows tur
> mucul error `WSL ... ERROR: CreateProcessCommon ... execvpe(/bin/bash)
> failed`, éta hartina WSL kainstal tapi can aya distro Linux-na. Teu
> kudu dibenerkeun -- cukup pake `.\demo.ps1` (PowerShell) gantina.
>
> **Troubleshooting (Windows)**: lamun mucul pesen *"Python was not
> found; run without arguments to install from the Microsoft Store"*,
> éta hartina alias kosong Windows Store, lain Python anu sabenerna.
> Pasang Python ti https://python.org (centang *"Add python.exe to
> PATH"* wektu instalasi), tuluy tutup-buka deui terminal-na.

### D. Ngabangun Installer (Executable Mandiri)

Pikeun ngahasilkeun hiji file executable mandiri nu bisa dijalankeun di
komputer lian **tanpa Python kainstal sama sakali**:

```bash
bash build_installer.sh        # Linux / macOS / Git Bash / WSL
```
```powershell
.\build_installer.ps1          # Windows PowerShell
```

Hasilna aya di `build/dist/sundac` (Linux/macOS) atawa
`build\dist\sundac.exe` (Windows, lamun skrip dijalankeun dina Windows).

```bash
./build/dist/sundac run examples/02_fungsi_prima.sun
```

> **Catetan**: PyInstaller ngahasilkeun executable nuturkeun OS/platform
> dimana skrip build dijalankeun. Lamun rék boga `.exe` Windows pikeun
> demo/video, jalankeun `build_installer.sh` (atawa paréntah
> `PyInstaller` di jerona) dina komputer Windows nu geus kainstal Python.

---

## 10. Conto Program & Kaluaran

Lihat folder `examples/` pikeun 4 conto lengkep:

1. **`01_halo_dunya.sun`** — Variabel, string, aritmatika basajan.
2. **`02_fungsi_prima.sun`** — `PANCEN` (fungsi + rekursi), `UPAMA/SABALIKNA`,
   `SALILA` (while), `PIKEUN..DINA` (for-in).
3. **`03_larik.sun`** — Larik (array), indeks, fungsi bawaan
   (`panjangna`, `pangluhurna`, `panghandapna`, `jumlahkeun`).
4. **`04_demo_optimasi.sun`** — Khusus mintonkeun Code Optimization
   (constant folding + dead code elimination).
5. **`05_contoh_error.sun`** — Khusus mintonkeun Penanganan Error
   (Semantic Analysis), dipake otomatis ku `demo.sh`.

Conto kaluaran `02_fungsi_prima.sun`:

```
Faktorial 7 = 5040
7 mangrupa wilangan prima.
Wilangan prima ti 2 nepi ka 30:
2
3
5
7
11
13
17
19
23
29
```

---

## 11. Penanganan Error (3 Lapis)

SUNDAC ngalaporkeun kasalahan kalayan ngaran tahap + posisi baris/kolom:

```
*** KOMPILASI GAGAL ***
Semantic: Kapanggih 3 kasalahan:
  - Semantic [baris 2]: Variabel 'b' teu acan dideklarasikeun (pake 'SIMPEN b = ...' heula)
  - Semantic [baris 4]: EUREUN (break) ngan sah dipake di jero perulangan SALILA/PIKEUN
  - Semantic [baris 9]: Pancen 'tambah' meryogikeun 2 argumen, tapi anu dibikeun 3
```

- **LexerError** — karakter teu dikenal, string/komentar teu ditutup.
- **ParserError** — struktur kalimat teu nuturkeun grammar (cth. `;` leungit).
- **SemanticError** — variabel/pancen teu dideklarasikeun, `break`/`return`
  salah panempatan, jumlah argumen teu cocog, jrrd.

---

## 12. Keterbatasan & Pengembangan Lanjutan

Sangkan tetep fokus jeung jelas pikeun tujuan akademis, sababaraha hal
ieu can/teu didukung sarta bisa jadi pamekaran salajengna:

- Teu aya sistem tipe statis (type checking masih dinamis, dipariksa
  ku Python interpreter wektu runtime, lain wektu Semantic Analysis).
- Teu aya `class`/struct, modul/`import`, atawa penanganan exception
  (`try/catch`) custom.
- Fungsi/pancen teu ngadukung *default parameter* atawa *variadic args*.
- Pancen anu silih panggil (mutual recursion) antar fungsi top-level
  ngan jalan lamun kahontal (dipanggil) ti jero fungsi séjén, sabab
  kode Python hasil generate nuturkeun aturan eksekusi top-to-bottom
  Python aslina (sarua persis jeung kumaha Python sorangan jalan).

---

## 13. Panutup

SUNDAC mangrupa proyék mini compiler nu mintonkeun sakabéh tahapan
kompilasi klasik — ti Lexer nepi ka Code Generation jadi installer —
kalayan "kulit" basa Sunda. Mugia bisa jadi conto kongkrit kumaha
hiji basa pemrograman dirarancang tur diimplementasikeun ti nol.

*Wilujeng diajar, hatur nuhun.* 🐯
