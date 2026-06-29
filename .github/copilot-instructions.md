# GitHub Copilot — DBA Oracle Context

DBA Flávio Melo (Oracle 19c/23ai, SQL Server, MongoDB, Linux). Ambiente INEP.

## Skills disponíveis

Skills de referência em `~/.claude/skills/` (OneDrive INEP) e `D:\work\.github\skills\`.
Copilot não invoca skills diretamente — use o conteúdo abaixo como contexto.

## Padrões de código

### Oracle SQL
- Views de diagnóstico: `V$SESSION`, `V$SQL`, `V$SYS_TIME_MODEL`, `GV$SESS_TIME_MODEL`
- Sempre usar bind variables — nunca literais em queries dinâmicas
- `FETCH FIRST N ROWS ONLY` em vez de `ROWNUM`
- `ROUND(..., 2)` em cálculos de GB/MB; `/1024/1024/1024` para bytes→GB

### RMAN
- Sempre `BACKUP DATABASE PLUS ARCHIVELOG`
- `CONFIGURE CONTROLFILE AUTOBACKUP ON` antes do primeiro backup
- `BACKUP VALIDATE` antes de qualquer restore em produção

### Data Pump
- Prefixo de arquivo: `dba_flavio-exp_<SCHEMA>_%U.dmp`
- Parâmetros obrigatórios: `METRICS=Y LOGTIME=ALL EXCLUDE=STATISTICS`
- Paralelismo: ≤16GB→1, ≤50GB→2, ≤100GB→4, >100GB→8

### Data Guard
- Sempre verificar `apply lag` e `transport lag` antes de switchover
- `ALTER DATABASE COMMIT TO SWITCHOVER TO STANDBY` no Primary primeiro
- Nunca `ACTIVATE STANDBY DATABASE` sem confirmar que Primary está inacessível

## Estrutura de diagnóstico de performance

Fluxo: Time Model → CPU Session → AWR/ASH → SQL Diagnosis

1. `V$SYS_TIME_MODEL` — onde está o DB time?
2. Se DB CPU alto → `GV$SESS_TIME_MODEL` delta (s_cpu) — qual sessão?
3. Se waits dominam → AWR/ASH — qual wait event?
4. SQL problemático → `DBMS_XPLAN.DISPLAY_CURSOR` com `ALLSTATS LAST +ADAPTIVE`

## Convenções gerais

- Português brasileiro em comentários e documentação
- Commits: Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`)
- Tabelas markdown com números alinhados à direita (`---:`)
- Findings ranqueados por impacto em DB Time, não por curiosidade técnica
