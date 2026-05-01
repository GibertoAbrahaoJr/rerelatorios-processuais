# Relatórios Processuais IA — App Web para Hospedagem

Este é um aplicativo web para ser hospedado e acessado por domínio, por exemplo:

`https://relatorios.seudominio.com.br`

## O que já faz

- Login com usuário e senha.
- Upload de Excel/CSV.
- Leitura da coluna obrigatória `numero_processo`.
- Campos opcionais: `cliente`, `pasta`, `observacao`.
- Identificação básica de tribunal pelo número CNJ.
- Geração de relatório Word individual por processo.
- Download individual e ZIP com todos os relatórios.
- Estrutura pronta para DataJud/CNJ.
- Estrutura pronta para IA.

## O que ainda não está ativado

- Consulta real aos tribunais com certificado digital.
- Consulta de autos sigilosos.
- IA real via OpenAI API.

Esses pontos exigem chaves, credenciais, certificados e validação técnica/jurídica por tribunal.

## Rodar localmente

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Acesse:

`http://127.0.0.1:8000`

Login inicial:

- Usuário: `admin`
- Senha: `troque-esta-senha`

## Subir no Render

1. Crie conta no Render.
2. Crie um novo Web Service.
3. Envie este projeto para um GitHub ou faça deploy pelo repositório.
4. O Render detectará o `render.yaml`.
5. Altere a variável `APP_PASSWORD` para uma senha forte.
6. Depois aponte seu domínio para o serviço.

## Variáveis importantes

- `APP_USERNAME`: usuário de login.
- `APP_PASSWORD`: senha de login.
- `SESSION_SECRET`: chave interna de sessão.
- `DATA_PROVIDER`: `mock` ou `datajud`.
- `DATAJUD_ENABLED`: `true` ou `false`.
- `DATAJUD_API_KEY`: chave do DataJud, se aplicável.
- `OPENAI_API_KEY`: chave da OpenAI, para futura análise por IA.

## Modelo de planilha

```csv
numero_processo,cliente,pasta,observacao
1001234-56.2024.8.26.0100,Cliente A,Pasta 001,Analisar urgência
0009876-12.2023.5.15.0001,Cliente B,Pasta 002,Verificar execução
```
