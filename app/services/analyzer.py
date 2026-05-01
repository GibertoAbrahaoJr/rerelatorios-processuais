def analyze(data: dict) -> dict:
    movs = data.get("movimentacoes", [])
    ultimas = [m.get("texto", "") if isinstance(m, dict) else str(m) for m in movs[-5:]]
    return {
        "resumo_executivo": (
            f"Processo {data.get('numero_processo')} cadastrado para acompanhamento. "
            f"Tribunal provável: {data.get('tribunal')}. Classe: {data.get('classe')}."
        ),
        "situacao_atual": "A situação final depende da consulta real das movimentações e, quando aplicável, dos autos.",
        "pontos_de_atencao": "Validar movimentações relevantes, prazos pendentes, decisões recentes e necessidade de acesso com certificado digital.",
        "recomendacao": "Usar esta versão para triagem e geração padronizada. Para parecer ao cliente, conferir fonte oficial/consulta real.",
        "ultimas_movimentacoes": ultimas,
    }
