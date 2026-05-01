from fastapi import FastAPI, Request, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
import shutil, uuid, zipfile

from app.config import settings
from app.services.excel_reader import read_processes
from app.services.provider import fetch_process_data
from app.services.analyzer import analyze
from app.services.report import generate_docx, REPORT_DIR

app = FastAPI(title=settings.APP_NAME)
app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
UPLOAD_DIR = Path("app/storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def current_user(request: Request):
    if not request.session.get("user"):
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return request.session.get("user")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": ""})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == settings.APP_USERNAME and password == settings.APP_PASSWORD:
        request.session["user"] = username
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Usuário ou senha inválidos."})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, user=Depends(current_user)):
    return templates.TemplateResponse("index.html", {"request": request, "user": user, "app_name": settings.APP_NAME})

@app.post("/upload", response_class=HTMLResponse)
async def upload(request: Request, file: UploadFile = File(...), user=Depends(current_user)):
    suffix = Path(file.filename).suffix.lower()
    saved = UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"
    with saved.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    processes = read_processes(str(saved))
    items = []
    report_paths = []
    for item in processes:
        data = await fetch_process_data(item)
        analysis = analyze(data)
        report_path = generate_docx(data, analysis)
        report_paths.append(report_path)
        items.append({
            "numero": data.get("numero_processo"),
            "cliente": data.get("cliente", ""),
            "tribunal": data.get("tribunal", ""),
            "classe": data.get("classe", ""),
            "fonte": data.get("fonte", ""),
            "resumo": analysis.get("resumo_executivo", ""),
            "report_file": Path(report_path).name,
        })

    zip_name = f"relatorios_{uuid.uuid4().hex[:8]}.zip"
    zip_path = REPORT_DIR / zip_name
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rp in report_paths:
            zf.write(rp, arcname=Path(rp).name)

    return templates.TemplateResponse("results.html", {"request": request, "items": items, "count": len(items), "zip_file": zip_name})

@app.get("/reports/{filename}")
async def download_report(filename: str, user=Depends(current_user)):
    path = REPORT_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    return FileResponse(path, filename=filename)

@app.get("/health")
async def health():
    return {"status": "ok"}
