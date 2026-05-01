from __future__ import annotations

from datetime import datetime
import re
from typing import Any

import httpx
from app.config import settings

BASE_URL = "https://api-publica.datajud.cnj.jus.br"

# Mapas principais com base no padrão CNJ do número processual: NNNNNNN-DD.AAAA.J.TR.OOOO
STATE_COURTS = {
    "01": ("TJAC", "api_publica_tjac"), "02": ("TJAL", "api_publica_tjal"),
    "03": ("TJAP", "api_publica_tjap"), "04": ("TJAM", "api_publica_tjam"),
    "05": ("TJBA", "api_publica_tjba"), "06": ("TJCE", "api_publica_tjce"),
    "07": ("TJDFT", "api_publica_tjdft"), "08": ("TJES", "api_publica_tjes"),
    "09": ("TJGO", "api_publica_tjgo"), "10": ("TJMA", "api_publica_tjma"),
    "11": ("TJMT", "api_publica_tjmt"), "12": ("TJMS", "api_publica_tjms"),
    "13": ("TJMG", "api_publica_tjmg"), "14": ("TJPA", "api_publica_tjpa"),
    "15": ("TJPB", "api_publica_tjpb"), "16": ("TJPR", "api_publica_tjpr"),
    "17": ("TJPE", "api_publica_tjpe"), "18": ("TJPI", "api_publica_tjpi"),
    "19": ("TJRJ", "api_publica_tjrj"), "20": ("TJRN", "api_publica_tjrn"),
    "21": ("TJRS", "api_publica_tjrs"), "22": ("TJRO", "api_publica_tjro"),
    "23": ("TJRR", "api_publica_tjrr"), "24": ("TJSC", "api_publica_tjsc"),
    "25": ("TJSE", "api_publica_tjse"), "26": ("TJSP", "api_publica_tjsp"),
    "27": ("TJTO", "api_publica_tjto"),
}

FEDERAL_COURTS = {
    "01": ("TRF1", "api_publica_trf1"), "02": ("TRF2", "api_publica_trf2"),
    "03": ("TRF3", "api_publica_trf3"), "04": ("TRF4", "api_publica_trf4"),
    "05": ("TRF5", "api_publica_trf5"), "06": ("TRF6", "api_publica_trf6"),
}

# TRT 1 a 24. O DataJud usa api_publica_trt1, api_publica_trt2 etc.
LABOR_COURTS = {f"{i:02d}": (f"TRT{i}", f"api_publica_trt{i}") for i in range(1, 25)}

ELECTORAL_COURTS = {
    "01": ("TSE", "api_publica_tse"), "02": ("TREAC", "api_publica_tre-ac"),
}


def only_digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def split_cnj_number(numero: str) -> dict[str, str]:
    digits = only_digits(numero)
    if len(digits) != 20:
        return {"valid": False, "digits": digits}
    return {
        "valid": True,
        "digits": digits,
        "sequencial": digits[0:7],
        "digito": digits[7:9],
        "ano": digits[9:13],
        "justica": digits[13:14],
        "tribunal": digits[14:16],
        "origem": digits[16:20],
    }


def infer_tribunal(numero: str) -> dict[str, str | None]:
    parsed = split_cnj_number(numero)
    if not parsed.get("valid"):
        return {"nome": "Número CNJ inválido ou incompleto", "alias": None, "endpoint": None, "digits": parsed.get("digits", "")}

    justica = parsed["justica"]
    tribunal_code = parsed["tribunal"]
    table = None
    if justica == "8":
        table = STATE_COURTS
    elif justica == "5":
        table = LABOR_COURTS
    elif justica == "4":
        table = FEDERAL_COURTS

    if not table or tribunal_code not in table:
        return {"nome": f"Não identificado automaticamente J={justica}, TR={tribunal_code}", "alias": None, "endpoint": None, "digits": parsed["digits"]}

    nome, alias = table[tribunal_code]
    return {"nome": nome, "alias": alias, "endpoint": f"{BASE_URL}/{alias}/_search", "digits": parsed["digits"]}


async def fetch_process_data(item: dict) -> dict:
    numero = item["numero_processo"]
    tribunal_info = infer_tribunal(numero)

    if settings.DATA_PROVIDER.lower() == "datajud" and settings.DATAJUD_ENABLED:
        data = await fetch_datajud(numero, tribunal_info)
        if data:
            data.update({k: v for k, v in item.items() if v})
            return data

    return fallback_data(item, tribunal_info, "Consulta DataJud não retornou dados ou não está ativada.")


def fallback_data(item: dict, tribunal_info: dict, motivo: str) -> dict:
    numero = item["numero_processo"]
    return {
        **item,
        "numero_processo": numero,
        "tribunal": tribunal_info.get("nome") or "Não identificado",
        "fonte": "DataJud/CNJ não localizado; fallback local",
        "classe": "A consultar",
        "assunto": "A consultar",
        "orgao_julgador": "A consultar",
        "grau": "A consultar",
        "data_distribuicao": "A consultar",
        "ultima_atualizacao": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "status_consulta": motivo,
        "movimentacoes": [
            {"data": datetime.now().strftime("%d/%m/%Y"), "texto": motivo},
            {"data": datetime.now().strftime("%d/%m/%Y"), "texto": "Verificar número CNJ, tribunal e disponibilidade do processo público no DataJud."},
        ],
    }


async def fetch_datajud(numero: str, tribunal_info: dict) -> dict | None:
    endpoint = tribunal_info.get("endpoint")
    digits = tribunal_info.get("digits") or only_digits(numero)
    if not endpoint or not digits:
        return fallback_data({"numero_processo": numero}, tribunal_info, "Não foi possível identificar endpoint DataJud pelo número do processo.")

    headers = {
        "Authorization": f"APIKey {settings.DATAJUD_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    # DataJud/Elasticsearch normalmente indexa numeroProcesso sem pontuação.
    body = {
        "size": 1,
        "query": {
            "bool": {
                "should": [
                    {"term": {"numeroProcesso": digits}},
                    {"match": {"numeroProcesso": digits}},
                    {"match": {"numeroProcesso": numero}},
                ],
                "minimum_should_match": 1,
            }
        },
        "sort": [{"@timestamp": {"order": "desc", "unmapped_type": "date"}}],
    }

    try:
        async with httpx.AsyncClient(timeout=settings.DATAJUD_TIMEOUT_SECONDS) as client:
            response = await client.post(endpoint, json=body, headers=headers)
            if response.status_code in {401, 403}:
                return fallback_data({"numero_processo": numero}, tribunal_info, f"DataJud recusou autenticação. Status {response.status_code}. Atualize DATAJUD_API_KEY no Render.")
            if response.status_code >= 400:
                return fallback_data({"numero_processo": numero}, tribunal_info, f"DataJud retornou erro HTTP {response.status_code} para {tribunal_info.get('nome')}.")
            payload = response.json()
    except Exception as exc:
        return fallback_data({"numero_processo": numero}, tribunal_info, f"Falha técnica ao consultar DataJud: {type(exc).__name__}.")

    hits = payload.get("hits", {}).get("hits", [])
    if not hits:
        return fallback_data({"numero_processo": numero}, tribunal_info, f"Processo não encontrado no DataJud para {tribunal_info.get('nome')}.")

    src = hits[0].get("_source", {})
    return normalize_datajud_source(numero, tribunal_info, src)


def value_name(obj: Any) -> str:
    if isinstance(obj, dict):
        return str(obj.get("nome") or obj.get("descricao") or obj.get("codigo") or "")
    return str(obj or "")


def normalize_list_names(items: Any) -> str:
    if not isinstance(items, list):
        return value_name(items)
    names = []
    for item in items:
        name = value_name(item)
        if name:
            names.append(name)
    return ", ".join(names) if names else "Não informado"


def normalize_movements(movimentos: Any) -> list[dict[str, str]]:
    if not isinstance(movimentos, list):
        return []
    normalized = []
    for mov in movimentos[-settings.DATAJUD_MAX_MOVIMENTOS:]:
        if not isinstance(mov, dict):
            normalized.append({"data": "", "texto": str(mov)})
            continue
        data = mov.get("dataHora") or mov.get("data") or ""
        nome = mov.get("nome") or mov.get("descricao") or ""
        complementos = []
        for key in ("complementosTabelados", "complementos", "movimentoLocal"):
            val = mov.get(key)
            if isinstance(val, list):
                complementos.extend([value_name(v) for v in val if value_name(v)])
            elif isinstance(val, dict) or isinstance(val, str):
                txt = value_name(val)
                if txt:
                    complementos.append(txt)
        texto = nome or str({k: v for k, v in mov.items() if k not in {"dataHora", "data"}})
        if complementos:
            texto = f"{texto} — {'; '.join(complementos)}"
        normalized.append({"data": data, "texto": texto})
    return normalized


def normalize_datajud_source(numero: str, tribunal_info: dict, src: dict) -> dict:
    movimentos = normalize_movements(src.get("movimentos", []))
    return {
        "numero_processo": numero,
        "tribunal": tribunal_info.get("nome") or "Não identificado",
        "fonte": "DataJud/CNJ - API Pública",
        "classe": value_name(src.get("classe")) or "Não informado",
        "assunto": normalize_list_names(src.get("assuntos")),
        "orgao_julgador": value_name(src.get("orgaoJulgador")) or "Não informado",
        "grau": src.get("grau") or src.get("nivelSigilo") or "Não informado",
        "data_distribuicao": src.get("dataAjuizamento") or "Não informado",
        "ultima_atualizacao": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "status_consulta": "Encontrado no DataJud/CNJ.",
        "movimentacoes": movimentos or [{"data": "", "texto": "Processo encontrado, mas sem movimentações retornadas pela API Pública."}],
    }
