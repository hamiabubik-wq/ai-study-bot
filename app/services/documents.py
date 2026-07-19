from io import BytesIO
from pathlib import Path
from pypdf import PdfReader
from docx import Document

def extract(data,filename,mime):
    s=Path(filename).suffix.lower()
    if s=='.pdf' or mime=='application/pdf': text='\n'.join(p.extract_text() or '' for p in PdfReader(BytesIO(data)).pages)
    elif s=='.docx': text='\n'.join(p.text for p in Document(BytesIO(data)).paragraphs)
    elif s in {'.txt','.md','.py','.js','.html','.css','.json','.csv','.java','.cpp','.cs','.php','.go','.rs'}: text=data.decode('utf-8',errors='replace')
    else: raise ValueError('Поддерживаются PDF, DOCX, TXT и текстовые файлы кода')
    if not text.strip(): raise ValueError('Не удалось извлечь текст')
    return text[:50000]
