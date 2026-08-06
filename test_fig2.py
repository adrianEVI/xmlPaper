from bs4 import BeautifulSoup

xml = """<?xml version='1.0' encoding='utf-8'?>
<article xmlns:mml="http://www.w3.org/1998/Math/MathML" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:ali="http://www.niso.org/schemas/ali/1.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" article-type="research-article" dtd-version="1.1" specific-use="sps-1.9" xml:lang="es">
<body>
    <disp-quote>
      <p><inline-graphic mime-subtype="png" mimetype="image" xlink:href="media/image1.png"/>
  Los contenidos de este artículo están bajo una licencia de Creative
  Commons Atribución No Comercial - Sin Obra Derivada 4.0
  Internacional</p>
    </disp-quote>
</body>
</article>"""

soup = BeautifulSoup(xml, 'xml')
body = soup.find('body')
print(f"body found: {body is not None}")
graphics = body.find_all(['inline-graphic', 'graphic'])
print(f"graphics found: {len(graphics)}")
for graphic in graphics:
    print(graphic.name)
