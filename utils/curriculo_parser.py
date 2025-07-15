import re
import PyPDF2

def extrair_texto_pdf(caminho_arquivo):
    with open(caminho_arquivo, 'rb') as f:
        leitor = PyPDF2.PdfReader(f)
        texto = ""
        for pagina in leitor.pages:
            texto += pagina.extract_text()
        return texto

def extrair_email(texto):
    padrao_email = r'[\w\.-]+@[\w\.-]+\.\w+'
    resultado = re.findall(padrao_email, texto)
    return resultado[0] if resultado else None

def extrair_linkedin(texto):
    padrao = r'(https?://(www\.)?linkedin\.com/in/[^\s]+)'
    resultado = re.findall(padrao, texto)
    return resultado[0][0] if resultado else None

def analisar_curriculo(caminho_pdf):
    texto = extrair_texto_pdf(caminho_pdf)
    email = extrair_email(texto)
    linkedin = extrair_linkedin(texto)
    
    return {
        'email': email,
        'linkedin': linkedin,
        'texto': texto[:500]  # só um trecho do texto como exemplo
    }
