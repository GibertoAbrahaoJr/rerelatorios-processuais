from datetime import datetime
import httpx
from app.config import settings

DATAJUD_ENDPOINTS = {
    "TJSP": "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search",
    "TRT15": "https://api-publica.datajud.cnj.jus.br/api_publica_trt15/_search",
    "TRT2": "https://api-publica.datajud.cnj.jus.br/api_publica_trt2/_search",
}

def infer_tribunal(numero: str) -> str:
    n = numero.replace("-", ".")
    if ".8.26." in n:
        return "TJSP"
    if ".5.15." in n:
        return "TRT15"
    if ".5.02." in n:
        return "TRT2"
    if ".4." in n:
        return "TRF/JF - identificar região"
    return "Não identificado automaticamente"

async def fetch_process_data(item: dict) -> dict:
    numero = item["numero_processo"]
    tribunal = infer_tribunal(numero)

    if settings.DATA_PROVIDER == "datajud" and settings.DATAJUD_ENABLED:
        data = await fetch_datajud(numero, tribunal)
        if data:
            data.update(item)
            return data

    return {
        **item,
        "numero_processo": numero,
        "tribunal": tribunal,
        "fonte": "Mock local / estrutura pronta para DataJud",
        "classe": "A consultar",
        "assunto": "A consultar",
        "orgao_julgador": "A consultar",
        "grau": "A consultar",
        "data_distribuicao": "A consultar",
        "ultima_atualizacao": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "movimentacoes": [
            {"data": datetime.now().strftime("%d/%m/%Y"), "texto": "Processo importado da planilha."},
            {"data": datetime.now().strftime("%d/%m/%Y"), "texto": "Consulta real ainda não ativada neste ambiente."},
            {"data": datetime.now().strftime("%d/%m/%Y"), "texto": "Relatório gerado em formato padronizado."},
        ],
    }

async def fetch_datajud(numero: str, tribunal: str) -> dict | None:
    endpoint = DATAJUD_ENDPOINTS.get(tribunal)
    if not endpoint:
        return None
    headers = {"Authorization": f"APIKey {settings.DATAJUD_API_KEY}"} if settings.DATAJUD_API_KEY else {}
    body = {"query": {"match": {"numeroProcesso": numero}}}
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(endpoint, json=body, headers=headers)
            r.raise_for_status()
            payload = r.json()
            hits = payload.get("hits", {}).get("hits", [])
            if not hits:
                return None
            src = hits[0].get("_source", {})
            movs = src.get("movimentos", [])[-10:]
            return {
                "numero_processo": numero,
                "tribunal": tribunal,
                "fonte": "DataJud/CNJ",
                "classe": src.get("classe", {}).get("nome", "Não informado"),
                "assunto": ", ".join([a.get("nome", "") for a in src.get("assuntos", []) if isinstance(a, dict)]),
                "orgao_julgador": src.get("orgaoJulgador", {}).get("nome", "Não informado"),
                "grau": src.get("grau", "Não informado"),
                "data_distribuicao": src.get("dataAjuizamento", "Não informado"),
                "ultima_atualizacao": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "movimentacoes": [{"data": m.get("dataHora", ""), "texto": m.get("nome", str(m))} for m in movs],
            }
    except Exception:
        return None
