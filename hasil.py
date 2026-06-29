# ====================================================================
# Kode Python ieu di-generate otomatis ku Kompiler SUNDAC
# tina kode sumber Basa Sunda (.sun) -- ulah diédit langsung.
# ====================================================================

def faktorial(n):
    if (n <= 1):
        return 1
    return (n * faktorial((n - 1)))

def prima(n):
    if (n < 2):
        return False
    i = 2
    while ((i * i) <= n):
        if ((n % i) == 0):
            return False
        i = (i + 1)
    return True

angka = 7
print('Faktorial', angka, '=', faktorial(angka))
if prima(angka):
    print(angka, 'mangrupa wilangan prima.')
else:
    print(angka, 'lain wilangan prima.')
print('Wilangan prima ti 2 nepi ka 30:')
for n in range(2, 31):
    if prima(n):
        print(n)
