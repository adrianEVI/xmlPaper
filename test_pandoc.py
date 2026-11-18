import requests
import os

API_URL = "http://localhost:8000/convert"
DOCX_FILE = "sample_paper.docx"
XML_OUTPUT = "output_paper_jats.xml"

def process_docx_with_api():
    """Envía el DOCX a nuestra API y guarda el resultado XML"""
    if not os.path.exists(DOCX_FILE):
        print(f"Error: '{DOCX_FILE}' no encontrado. Por favor coloca un archivo de Word de prueba con ese nombre en este directorio.")
        return

    print(f"Enviando {DOCX_FILE} a la API ({API_URL})...")
    
    with open(DOCX_FILE, 'rb') as f:
        files = {'file': (DOCX_FILE, f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
        
        try:
            response = requests.post(API_URL, files=files, timeout=300)
            
            if response.status_code == 200:
                with open(XML_OUTPUT, 'wb') as xml_file:
                    xml_file.write(response.content)
                print(f"¡Éxito! El archivo XML ha sido guardado como: {XML_OUTPUT}")
            else:
                print(f"Error al procesar. Código HTTP: {response.status_code}")
                print("Respuesta de la API:", response.text)
        except requests.exceptions.RequestException as e:
            print(f"Error de conexión: {e}")
            print("Asegúrate de que la API de FastAPI esté corriendo (ej. con 'uvicorn main:app').")

def process_pdf_with_api():
    """Envía el PDF a nuestra API y guarda el resultado XML"""
    PDF_FILE = "sample_paper.pdf"
    if not os.path.exists(PDF_FILE):
        print(f"Error: '{PDF_FILE}' no encontrado. Por favor coloca un archivo PDF de prueba con ese nombre en este directorio.")
        return

    print(f"Enviando {PDF_FILE} a la API ({API_URL})...")
    
    with open(PDF_FILE, 'rb') as f:
        files = {'file': (PDF_FILE, f, 'application/pdf')}
        
        try:
            response = requests.post(API_URL, files=files, timeout=300)
            
            if response.status_code == 200:
                with open(XML_OUTPUT, 'wb') as xml_file:
                    xml_file.write(response.content)
                print(f"¡Éxito! El archivo XML desde PDF ha sido guardado como: {XML_OUTPUT}")
            else:
                print(f"Error al procesar PDF. Código HTTP: {response.status_code}")
                print("Respuesta de la API:", response.text)
        except requests.exceptions.RequestException as e:
            print(f"Error de conexión: {e}")
            print("Asegúrate de que la API de FastAPI esté corriendo (ej. con 'uvicorn main:app').")

if __name__ == "__main__":
    print("Probando conversión DOCX...")
    process_docx_with_api()
    print("\nProbando conversión PDF...")
    process_pdf_with_api()
