def analyze(data: dict) -> dict:
    movs = data.get("movimentacoes", [])
    fonte = data.get("fonte", "")
    encontrado = "DataJud/CNJ - API Pública" in fonte

    ultimas = [m.get("texto", "") if isinstance(m, dict) else str(m) for m in movs[-5:]]
    ultimo_txt = ultimas[-1] if ultimas else "Sem movimentação retornada."

    if encontrado:
        resumo = (
            f"Processo {data.get('numero_processo')} localizado no {data.get('tribunal')} via DataJud/CNJ. "
            f"Classe: {data.get('classe')}. Órgão julgador: {data.get('orgao_julgador')}. "
            f"Último andamento identificado: {ultimo_txt}"
        )
        situacao = "Dados extraídos da API Pública do DataJud/CNJ. Conferir no portal do tribunal antes de conclusão estratégica ou manifestação processual."
        pontos = "Verificar se há prazos, decisões recentes, segredo de justiça ou peças que exijam acesso direto ao tribunal com certificado digital."
    else:
        resumo = (
            f"Processo {data.get('numero_processo')} não teve dados públicos completos retornados pelo DataJud. "
            f"Tribunal provável: {data.get('tribunal')}. Status: {data.get('status_consulta', 'não informado')}."
        )
        situacao = "A consulta pública não retornou metadados suficientes. O caso deve ser conferido diretamente no portal do tribunal competente."
        pontos = "Pode haver erro no número, processo não público, indisponibilidade do DataJud, atraso de atualização ou necessidade de certificado digital."

    return {
        "resumo_executivo": resumo,
        "situacao_atual": situacao,
        "pontos_de_atencao": pontos,
        "recomendacao": "Usar o relatório como triagem automatizada. Para entrega final ao cliente, validar dados sensíveis e andamentos relevantes na fonte oficial do tribunal.",
        "ultimas_movimentacoes": ultimas,
    }
