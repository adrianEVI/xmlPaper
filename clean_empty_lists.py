import os
from bs4 import BeautifulSoup

def clean_lists_in_file(xml_path):
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'xml')
    modified = False

    for li in list(soup.find_all('list-item')):
        if not li.get_text(strip=True):
            li.decompose()
            modified = True
        elif not li.find(['p', 'def-list', 'list']):
            p_tag = soup.new_tag('p')
            p_tag.extend(list(li.contents))
            li.append(p_tag)
            modified = True

    for lst in list(soup.find_all('list')):
        if not lst.find_all('list-item') or not lst.get_text(strip=True):
            lst.decompose()
            modified = True

    if modified:
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        print(f"[CLEANED LISTS] {xml_path}")
    else:
        print(f"[OK LISTS] {xml_path}")

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
                    clean_lists_in_file(os.path.join(full_d, fname))

if __name__ == "__main__":
    main()
