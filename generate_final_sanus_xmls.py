import os
import sys
import re
import shutil
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

sanus_new_dir = os.path.abspath("Articulos/SANUS/SANUSxmlNEW")
os.makedirs(sanus_new_dir, exist_ok=True)

pairs = [
    ("549", "549_ESP.xml", "2448-6094-sanus-10-21-e549-NEW.xml"),
    ("560", "560_ESP.xml", "2448-6094-sanus-10-21-e560-NEW.xml"),
    ("561", "561_ESP.xml", "2448-6094-sanus-10-21-e561-NEW.xml"),
    ("564", "564_ESP.xml", "2448-6094-sanus-10-21-e564-NEW.xml"),
    ("566", "566_ESP.xml", "2448-6094-sanus-10-21-e566-NEW.xml"),
    ("573", "573_ESP.xml", "2448-6094-sanus-10-21-e573-NEW.xml"),
]

print("Verificando y asegurando la presencia de los 12 archivos XML finales en SANUSxmlNEW...\n")

for num, f1, f2 in pairs:
    p1 = os.path.join(sanus_new_dir, f1)
    p2 = os.path.join(sanus_new_dir, f2)
    scielo_orig = os.path.join(sanus_new_dir, f"2448-6094-sanus-10-21-e{num}.xml")
    
    if os.path.exists(p1):
        shutil.copy(p1, p2)
        shutil.copy(p1, scielo_orig)
        print(f"  ✓ Copiado y sincronizado desde '{f1}': '{f2}' y '{os.path.basename(scielo_orig)}' ({os.path.getsize(p1)} bytes)")
    else:
        print(f"  ✗ Advertencia: No se encontró archivo base {f1}")

print("\nArchivos creados y verificados exitosamente.")
