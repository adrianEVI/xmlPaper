from bs4 import BeautifulSoup

xml = """<?xml version='1.0' encoding='utf-8'?>
<body>
    <disp-quote>
      <p><inline-graphic mime-subtype="png" mimetype="image" xlink:href="media/image1.png"/>
  Los contenidos de este artículo están bajo una licencia de Creative
  Commons Atribución No Comercial - Sin Obra Derivada 4.0
  Internacional</p>
    </disp-quote>
</body>"""

soup = BeautifulSoup(xml, 'xml')

def format_figures(soup: BeautifulSoup):
    body = soup.find('body')
    if not body:
        return
        
    fig_counter = 1
    for graphic in body.find_all(['inline-graphic', 'graphic']):
        if graphic.find_parent('fig'):
            continue
            
        parent = graphic.parent
        
        fig = soup.new_tag('fig', id=f"f{fig_counter}")
        label = soup.new_tag('label')
        label.string = f"Figura {fig_counter}"
        fig.append(label)
        
        caption = soup.new_tag('caption')
        title = soup.new_tag('title')
        
        text_content = ""
        if parent and parent.name == 'p':
            text_content = parent.get_text(strip=True)
            
        if text_content and len(text_content) < 200:
            title.string = text_content
            caption.append(title)
            fig.append(caption)
            
            # Using dict mapping instead of kwargs to avoid reserved/invalid characters
            new_graphic = soup.new_tag('graphic', **graphic.attrs)
            fig.append(new_graphic)
            
            parent.replace_with(fig)
        else:
            title.string = f"Figura {fig_counter}"
            caption.append(title)
            fig.append(caption)
            
            new_graphic = soup.new_tag('graphic', **graphic.attrs)
            fig.append(new_graphic)
            
            graphic.replace_with(fig)
            
        fig_counter += 1

format_figures(soup)
print(soup.prettify())
