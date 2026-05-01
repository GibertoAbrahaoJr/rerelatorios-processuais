# Agente Local TJSP - MVP

Este agente roda na sua máquina e abre o Chrome local para consultar o e-SAJ/TJSP.

## Instalação

No Terminal, dentro desta pasta:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Rodar o agente

```bash
uvicorn agente_tjsp:app --host 127.0.0.1 --port 5005
```

## Testar se está online

Abra no navegador:

```text
http://127.0.0.1:5005/status
```

## Consulta pública TJSP

Substitua pelo número real:

```text
http://127.0.0.1:5005/consultar-publico?numero_processo=1001234-56.2024.8.26.0100
```

## Consulta restrita / certificado

```text
http://127.0.0.1:5005/consultar-restrito?numero_processo=1001234-56.2024.8.26.0100
```

Essa rota abre o Chrome para login no e-SAJ com certificado. A extração automática de peças restritas precisa ser implementada depois de validarmos o fluxo real de login e as telas exibidas para seu certificado.

## Observação

Este MVP não burla login, captcha, restrições do tribunal, sigilo processual ou permissões. Ele usa o navegador local autenticado pelo próprio advogado.
