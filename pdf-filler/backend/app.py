import os
import json
import shutil
import base64
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import fitz  # PyMuPDF
from docling.document_converter import DocumentConverter
import ollama

# Local imports
from . import database

app = FastAPI()

# Zezwolenie na CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ścieżki i inicjalizacja
DATA_DIR = "/app/data"
if not os.path.exists("/app"):
    DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

database.init_db()

# Montowanie plików statycznych (frontendu)
FRONTEND_DIR = "/app/frontend"
if not os.path.exists("/app"):
    FRONTEND_DIR = "frontend"
# Tymczasowo wyłączone jeśli pliki frontendowe nie istnieją by uniknąć błędu startu
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
ollama_client = ollama.Client(host=OLLAMA_HOST)
# Zakładamy lekki model - dostosuj nazwę do wybranego, np. qwen2.5:1.5b, llama3.2:3b
MODEL_NAME = "llama3.2:1b" 

# Prosta "pamięć" sesji by nie analizować pliku za każdym razem
sessions = {}

class ChatRequest(BaseModel):
    session_id: str
    message: str
    profile_name: str

class TextBlock(BaseModel):
    text: str
    x: float
    y: float
    page: int

class GenerateRequest(BaseModel):
    session_id: str
    blocks: List[TextBlock]
    compress: bool = False

@app.get("/profiles")
def get_profiles():
    return {"profiles": database.get_all_profiles()}

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...), fast_mode: bool = Form(False)):
    session_id = os.urandom(8).hex()
    file_path = os.path.join(UPLOADS_DIR, f"{session_id}.pdf")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Konwersja na obrazek do podglądu (pierwsza strona dla uproszczenia, można rozbudować)
    doc = fitz.open(file_path)
    page = doc.load_page(0)
    pix = page.get_pixmap()
    img_path = os.path.join(UPLOADS_DIR, f"{session_id}.png")
    pix.save(img_path)
    
    # Przekazanie obrazu w Base64 by front-end łatwo go wczytał
    with open(img_path, "rb") as img_file:
        img_b64 = base64.b64encode(img_file.read()).decode("utf-8")
        
    # Uruchomienie ekstrakcji
    if fast_mode:
        markdown_text = ""
        for p in fitz.open(file_path):
            markdown_text += p.get_text() + "\n\n"
    else:
        converter = DocumentConverter()
        result = converter.convert(file_path)
        markdown_text = result.document.export_to_markdown()
    
    sessions[session_id] = {
        "file_path": file_path,
        "markdown": markdown_text,
        "history": []
    }
    
    return {
        "session_id": session_id, 
        "image_b64": img_b64, 
        "width": page.rect.width, 
        "height": page.rect.height
    }

@app.post("/chat")
def chat_with_model(req: ChatRequest):
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = sessions[req.session_id]
    markdown = session["markdown"]
    
    # Pobierz zapisane dane profilu
    profile_data = database.get_user_data(req.profile_name)
    profile_info = json.dumps(profile_data, ensure_ascii=False) if profile_data else "Brak zapisanych danych."
    
    system_prompt = f"""
Jesteś inteligentnym asystentem pomagającym krok po kroku wypełnić dokument PDF. 
Oto treść wyciągnięta z dokumentu:
{markdown}

Znasz już pewne informacje o użytkowniku (profil: {req.profile_name}):
{profile_info}

Twoim zadaniem jest przeanalizowanie dokumentu i zadanie użytkownikowi pytań o brakujące dane.
Zadawaj pytania jedno po drugim. Bądź zwięzły i pomocny. Pisz po polsku.
Jeśli jakaś wartość jest już znana (z zapisanych danych), zaproponuj jej użycie.
Na sam koniec, jeśli masz już daną odpowiedź, potwierdź to i powiedz użytkownikowi by 'złapał i upuścił' wygenerowany blok na dokumencie.
Aby wygenerować dla niego "klocek" do złapania, zakończ swoją wiadomość formatem: [KLOCEK: Tutaj treść klocka] (np. [KLOCEK: Jan Kowalski]).
UWAGA: Jeśli użytkownik stwierdzi, że chce pominąć dane pole, zostawić je puste lub wykreślić, po prostu to zaakceptuj. W takim przypadku NIE GENERUJ żadnego formatu [KLOCEK: ...], tylko przejdź do kolejnego pytania.
"""
    
    messages = [{"role": "system", "content": system_prompt}] + session["history"]
    messages.append({"role": "user", "content": req.message})
    
    # Jeśli użytkownik podał nowe dane, zróbmy bardzo uproszczone parsowanie i zapisanie do bazy, 
    # w pełni profesjonalnym rozwiązaniu można tu dodać odrębny krok LLM wyciągający jsona
    # Ale dla lekkości, po prostu dodamy do bazy jeśli jest w formacie klucz: wartość
    if ":" in req.message and len(req.message.split(":")) == 2:
        k, v = req.message.split(":")
        database.save_user_data(req.profile_name, k.strip(), v.strip())
    
    try:
        response = ollama_client.chat(model=MODEL_NAME, messages=messages)
        reply = response['message']['content']
        
        session["history"].append({"role": "user", "content": req.message})
        session["history"].append({"role": "assistant", "content": reply})
        
        return {"reply": reply}
    except Exception as e:
        return {"reply": f"Błąd połączenia z modelem Ollama: {str(e)}"}

@app.post("/generate")
def generate_pdf(req: GenerateRequest):
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    file_path = sessions[req.session_id]["file_path"]
    out_path = os.path.join(UPLOADS_DIR, f"{req.session_id}_filled.pdf")
    
    doc = fitz.open(file_path)
    # Nakładanie tekstu na PDF
    for block in req.blocks:
        page = doc.load_page(block.page)
        # pypdf/fitz: insert_text(point, text, fontsize=12, fontname="helv")
        # Współrzędne z frontendu muszą odpowiadać proporcjom
        page.insert_text((block.x, block.y), block.text, fontsize=12, color=(0,0,0))
        
    if req.compress:
        doc.save(out_path, garbage=4, deflate=True)
    else:
        doc.save(out_path)
    
    return FileResponse(out_path, filename="Wypelniony_Dokument.pdf")

@app.get("/")
def read_root():
    # Zwraca główny plik frontendu jeśli istnieje, by udostępniać z jednego portu
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "API is running. Frontend not found yet."}
