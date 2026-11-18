import os
import re

def fix_hrefs_in_file(xml_path):
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = re.sub(r'(?<!xlink:)\bhref\s*=\s*', 'xlink:href=', content)
    if new_content != content:
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"[FIXED HREFS] {xml_path}")
    else:
        print(f"[OK HREFS] {xml_path}")

def main():
    dirs = [
        "Articulos/SANUS/SANUSxml",
        "Articulos/SANUS/SANUSxmlNEW"
    ]
    for d in dirs:
        full_d = os.path.abspath(d)
        if os.path.exists(full_d):
            for fname in os.listdir(full_d):
                if fname.endswith(".xml"):
                    fix_hrefs_in_file(os.path.join(full_d, fname))

if __name__ == "__main__":
    main()
