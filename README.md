# Gerenciador de Leads B2B (LeadFlow)

CRUD local para gerenciar **leads, campanhas**, cidades/bairros e nichos de prospecção.
Tem busca, filtros (cidade, UF, nicho, status), status editável no funil
(novo → contato feito → proposta enviada → reunião marcada → fechado/perdido),
links clicáveis por lead (e-mail, site, LinkedIn, WhatsApp) e exportar/importar JSON.

Os dados ficam em **SQLite** (`gerenciador.db`), que é a fonte principal; o navegador
guarda só uma cópia de apoio. Persistem entre navegadores e sobrevivem a reinícios.

## Rodar

```bash
python3 server.py       # sobe o servidor em segundo plano
# ou: python3 ensure_server.py   (sobe se estiver parado e confirma que responde)
```

Abra http://localhost:8642/ — requisito: Python 3 (padrão no macOS/Linux), sem dependências externas.

Para usar em outra máquina da rede, o servidor escuta só em `127.0.0.1` por padrão
(linha final de `server.py`). Troque para `0.0.0.0` só em rede confiável.

## Arquivos

| Arquivo | Papel |
|---|---|
| `index.html` | interface completa (CSS e JS embutidos, sem build) |
| `server.py` | HTTP + SQLite (`/api/state`, `/api/ping`, `/api/leads/import`) |
| `ensure_server.py` | sobe o servidor se preciso e confirma que responde |
| `gerenciador.db` | banco de dados, criado na primeira execução (não vai para o Git) |

## Banco e filtros

O SQLite é a fonte principal: a tela carrega de `/api/state` ao abrir e recarrega quando
você volta para a aba. Filtros e menus são montados a partir desses dados — cidades e
nichos cadastrados, mais os que aparecem em leads e campanhas. Para acrescentar uma opção
nos filtros, cadastre no painel (aba Cidades/Nichos) ou insira no banco; nada fica fixo no HTML.

A lista inicial de 20 cidades e 5 nichos (`SEED_CIDADES`/`SEED_NICHOS` em `index.html`)
serve só para a primeira carga quando o banco ainda não existe.

## Instalar nos alunos

**Skill (recomendado):** cole no chat do OpenBot:

```
Instale a skill "gerenciador-leads" (https://github.com/andrealencarz/openbot-skill-gerenciador-leads)
e prepare o dashboard na minha máquina.
```

**Prompt simples:** cole no chat do OpenBot:

```
Crie o "Gerenciador de Leads B2B" na minha máquina:
1. Clone https://github.com/andrealencarz/openbot-gerenciador-leads em ~/gerenciador-leads
   (ou baixe index.html, server.py e ensure_server.py da branch main).
2. Rode python3 ensure_server.py dentro da pasta.
3. Abra http://localhost:8642 e confirme que carrega com 20 cidades e 5 nichos.
4. Diga como reabrir depois e onde ficam os dados (gerenciador.db).
```
