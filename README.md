# Relatórios Processuais IA — App Web com DataJud/CNJ

Aplicativo web para upload de Excel/CSV com processos, consulta pública via DataJud/CNJ e geração de relatórios em Word.

## O que esta versão faz

- Login privado.
- Upload de planilha `.xlsx`, `.xls` ou `.csv`.
- Leitura da coluna obrigatória `numero_processo`.
- Identificação automática do tribunal pelo número CNJ.
- Consulta real à API Pública do DataJud/CNJ.
- Exibição dos últimos andamentos retornados pela API.
- Geração de relatório Word individual e ZIP com todos os relatórios.

## Modelo de planilha

Coluna obrigatória:

```csv
numero_processo
1504574-36.2024.8.26.0362
```

Colunas opcionais: `cliente`, `pasta`, `observacao`.

## Variáveis de ambiente no Render

Em **Render > Environment**, configure:

```env
APP_USERNAME=admin
APP_PASSWORD=sua-senha-forte
SESSION_SECRET=uma-chave-secreta-grande
DATA_PROVIDER=datajud
DATAJUD_ENABLED=true
DATAJUD_API_KEY=cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw==
```

A `DATAJUD_API_KEY` acima é a chave pública divulgada na Wiki oficial do DataJud/CNJ na data de criação desta versão. O CNJ pode alterá-la; nesse caso, basta atualizar a variável no Render.

## Start Command no Render

Use exatamente:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Limitações desta versão

A consulta é feita via API Pública DataJud/CNJ, que retorna metadados de processos públicos. Processos sigilosos, peças, documentos e detalhes disponíveis apenas mediante login/certificado digital exigem uma próxima etapa de integração específica com PJe/e-SAJ/eproc ou portal do tribunal.
