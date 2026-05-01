from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import re

app = FastAPI(title="Agente Local TJSP", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def normalizar_numero(numero: str) -> str:
    return re.sub(r"\D", "", numero or "")

def formatar_cnj(numero: str) -> str:
    n = normalizar_numero(numero)
    if len(n) != 20:
        return numero
    return f"{n[0:7]}-{n[7:9]}.{n[9:13]}.{n[13]}.{n[14:16]}.{n[16:20]}"

def extrair_dados_html(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    def txt(selector: str):
        el = soup.select_one(selector)
        return el.get_text(" ", strip=True) if el else None

    dados = {
        "numero": txt("#numeroProcesso") or txt("span.numeroProcesso"),
        "classe": txt("#classeProcesso"),
        "area": txt("#areaProcesso"),
        "assunto": txt("#assuntoProcesso"),
        "data_distribuicao": txt("#dataHoraDistribuicaoProcesso"),
        "juiz": txt("#juizProcesso"),
        "valor_acao": txt("#valorAcaoProcesso"),
        "partes": [],
        "movimentacoes": [],
    }

    partes = soup.select("#tableTodasPartes tr") or soup.select("#tablePartesPrincipais tr")
    for p in partes:
        t = p.get_text(" ", strip=True)
        if t:
            dados["partes"].append(t)

    movs = soup.select("#tabelaTodasMovimentacoes tr") or soup.select("#tabelaUltimasMovimentacoes tr")
    for m in movs:
        data = m.select_one(".dataMovimentacao")
        desc = m.select_one(".descricaoMovimentacao")
        texto = m.get_text(" ", strip=True)
        if texto:
            dados["movimentacoes"].append({
                "data": data.get_text(" ", strip=True) if data else None,
                "descricao": desc.get_text(" ", strip=True) if desc else texto,
            })

    return dados

@app.get("/status")
def status():
    return {"status": "online", "servico": "Agente Local TJSP"}

@app.get("/consultar-publico")
def consultar_publico(numero_processo: str = Query(..., description="Número CNJ do processo")):
    """
    Consulta pública no e-SAJ/TJSP. Não acessa peças sigilosas nem área restrita.
    Serve como primeira validação do agente local.
    """
    numero_limpo = normalizar_numero(numero_processo)
    if len(numero_limpo) != 20:
        return {"status": "erro", "mensagem": "Número de processo inválido. Use número CNJ com 20 dígitos."}

    numero_digito_ano = numero_limpo[0:13]  # NNNNNNNDDYYYY
    foro = numero_limpo[16:20]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="chrome")
        page = browser.new_page()
        try:
            page.goto("https://esaj.tjsp.jus.br/cpopg/open.do", wait_until="domcontentloaded", timeout=60000)
            page.select_option("#cbPesquisa", "NUMPROC")
            page.fill("#numeroDigitoAnoUnificado", numero_digito_ano)
            page.fill("#foroNumeroUnificado", foro)
            page.click("#botaoConsultarProcessos")
            page.wait_for_load_state("domcontentloaded", timeout=60000)
            page.wait_for_timeout(2500)
            html = page.content()
            dados = extrair_dados_html(html)
            dados["numero_consultado"] = formatar_cnj(numero_limpo)
            dados["status"] = "ok"
            return dados
        except PlaywrightTimeoutError:
            return {"status": "erro", "mensagem": "Tempo esgotado ao consultar o TJSP. Tente novamente."}
        except Exception as e:
            return {"status": "erro", "mensagem": str(e)}
        finally:
            browser.close()

@app.get("/consultar-restrito")
def consultar_restrito(numero_processo: str = Query(..., description="Número CNJ do processo")):
    """
    Abre o portal e-SAJ para autenticação manual com certificado no Chrome.
    Esta versão inicial NÃO baixa peças automaticamente; ela abre o ambiente para validar login e sessão.
    A extração de documentos exige mapeamento específico de telas e permissões do advogado.
    """
    numero_limpo = normalizar_numero(numero_processo)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="chrome")
        page = browser.new_page()
        try:
            page.goto("https://esaj.tjsp.jus.br/esaj/portal.do?servico=740000", wait_until="domcontentloaded", timeout=60000)
            return {
                "status": "aberto",
                "mensagem": "Chrome aberto no portal e-SAJ. Faça o login com certificado digital. Depois será possível mapear a extração restrita.",
                "processo": formatar_cnj(numero_limpo),
            }
        except Exception as e:
            return {"status": "erro", "mensagem": str(e)}
