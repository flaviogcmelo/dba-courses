# CLAUDE.md — dba-courses

Repositório de cursos, imersões e materiais de estudo. Ambiente de estudo/laboratório, **não operacional**.

---

## Contexto

Este repositório reúne o material de todos os cursos e imersões (com IA) que Flávio participou: Oracle Data Guard, Patch & AutoUpgrade, Performance, Backup & Recovery, PostgreSQL, entre outros. Não há sistemas de produção, bancos de dados operacionais nem tickets INEP neste contexto.

- Não aplicar regras operacionais INEP (RITM, fnc_retorna_ambiente, etc.)
- Não usar MCPs de bancos de dados de produção — apenas labs/VMs de estudo
- Responder em português, foco didático
- Cada curso/imersão pode ter seu próprio `.claude/` e `CLAUDE.md` local com contexto específico (ex: `ImersaoPachUpgIA/CLAUDE.md`); quando presente, ele tem precedência sobre este arquivo dentro da respectiva pasta

## Estrutura

| Pasta | Conteúdo | Status |
|-------|----------|--------|
| `ImersaoDGIA/` | Imersão Data Guard com IA — MCP SQLcl já configurado, relatórios em `Reports/` | Em andamento |
| `ImersaoPachUpgIA/` | Imersão Oracle Patch & AutoUpgrade com IA — entregáveis, binários, `CLAUDE.md` próprio | Concluído |
| `ImersaoPerfIA/` | Imersão Performance Oracle com IA — desafios, labs, relatórios, docs | Concluído |
| `Imersão Oracle Backup Recovery/` | Curso Oracle RMAN / Backup & Recovery — relatórios, skills, certificado | Concluído |
| `Imersoes/BackupRecovery/` | Material legado/duplicado da imersão de Backup & Recovery (slides originais) | Legado |
| `CursoPostgres/` | Curso PostgreSQL — instalação PG18 em OL8, acesso remoto | Em andamento |
| `Postgres/` | Pasta reservada para materiais gerais de PostgreSQL | Vazio |
| `DBASobrinho/` | Scripts de monitoramento Data Guard (material de mentoria) | Referência |
| `Patch-Upgrade/` | Materiais brutos (zip/pptx) do curso de Patch & Upgrade | Referência |
| `PerfilEscritaLinkedin/` | Reservado para perfil de escrita usado pela skill `linkedin-post` | Vazio |
| `db-sample-schemas/` | Submodule oficial `oracle-samples/db-sample-schemas` — schemas de exemplo para labs | Submodule |

## Observações

- Arquivos grandes (vídeos `.mp4`, `.zip`, PDFs) são versionados normalmente neste repo; considerar Git LFS caso o tamanho cresça muito.
- `Imersoes/BackupRecovery/` duplica conteúdo já presente em `Imersão Oracle Backup Recovery/`; ao criar algo novo relacionado a Backup & Recovery, usar a pasta sem duplicidade (`Imersão Oracle Backup Recovery/`) e considerar consolidar/remover a legada no futuro.
