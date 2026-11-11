# Gerenciador de Cidades & Nichos (Buscador de Leads)

CRUD local para manter a lista de cidades, bairros e nichos de prospecção, com busca, filtros e status editável (não iniciada / em andamento / prospectada). Dados em **SQLite** (`gerenciador.db`), persistem entre navegadores.

## Rodar

```bash
python3 server.py
# abra http://localhost:8642/
```

Requisito: Python 3 (padrão no macOS/Linux). Sem dependências externas.

## Distribuição (prompt para alunos)

Cole no chat do OpenBot:

```
Crie um "Gerenciador de Cidades & Nichos" (CRUD de cidades/bairros/nichos com busca, filtros e status editável) na minha máquina:
1. Crie a pasta ~/gerenciador-leads e baixe os arquivos: https://raw.githubusercontent.com/andrealencarz/gerenciador-leads/main/index.html e https://raw.githubusercontent.com/andrealencarz/gerenciador-leads/main/server.py
2. Rode python3 server.py dentro da pasta (em segundo plano).
3. Abra http://localhost:8642 no navegador e confirme que carrega com 20 cidades e 5 nichos.
4. Diga como reabrir depois e onde ficam os dados (gerenciador.db).
```
