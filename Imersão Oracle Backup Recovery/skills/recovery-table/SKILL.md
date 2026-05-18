---
name: recovery-table
description: Recuperar uma tabela específica (ou conjunto de tabelas) em um banco Oracle 19c usando RMAN RECOVER TABLE, recurso introduzido no 12c que automatiza restore em instância auxiliar e import via Data Pump. Use sempre que o desafio envolver recuperar uma tabela perdida ou corrompida sem afetar o banco inteiro, fazer recovery point-in-time de uma tabela, usar RECOVER TABLE com UNTIL TIME/SCN, ou recuperar tabelas com nome remapeado (REMAP TABLE).
---

# Recovery Table (RMAN RECOVER TABLE)

## Objetivo

Recuperar uma ou mais tabelas específicas para um ponto no passado **sem afetar o banco inteiro**. O RMAN automatiza: criação de instância auxiliar temporária, restore parcial, recovery point-in-time, export via Data Pump da tabela e import no banco de produção.

Cenário típico: alguém fez `DELETE`/`DROP`/`TRUNCATE` por engano e o flashback table/query não cobre o caso (ex: storage não permite undo retenção suficiente, ou tabela com `PURGE`).

## Pré-requisitos

- Banco Oracle 12c+ (no 19c é totalmente suportado)
- Banco em modo **ARCHIVELOG**
- Backup RMAN cobrindo o ponto no tempo desejado
- Archived redo logs disponíveis entre o backup e o ponto-alvo
- Acesso `SYSDBA`
- Espaço em disco para a **auxiliary destination** (instância temporária) — aproximadamente o tamanho do tablespace SYSTEM, SYSAUX, UNDO, e do tablespace que contém a tabela

## Passo a passo

### 1. Identificar o ponto no tempo desejado

```sql
-- Pelo timestamp
SELECT TO_CHAR(SYSDATE, 'YYYY-MM-DD HH24:MI:SS') FROM dual;

-- Pelo SCN
SELECT current_scn FROM v$database;

-- Histórico recente
SELECT scn, time_dp FROM sys.smon_scn_time ORDER BY scn DESC FETCH FIRST 10 ROWS ONLY;
```

### 2. Criar diretório para a auxiliary destination

```bash
mkdir -p /u01/aux_dest
chown oracle:oinstall /u01/aux_dest
```

### 3. Executar o RECOVER TABLE

**Caso A — restaurar uma tabela com o mesmo nome (sobrescreve a atual):**
```rman
RECOVER TABLE HR.EMPLOYEES
  UNTIL TIME "TO_DATE('2026-05-14 09:00:00','YYYY-MM-DD HH24:MI:SS')"
  AUXILIARY DESTINATION '/u01/aux_dest';
```

**Caso B — restaurar com nome diferente (mais seguro):**
```rman
RECOVER TABLE HR.EMPLOYEES
  UNTIL SCN 1500000
  AUXILIARY DESTINATION '/u01/aux_dest'
  REMAP TABLE HR.EMPLOYEES:HR.EMPLOYEES_RECOVERED;
```

**Caso C — recuperar múltiplas tabelas:**
```rman
RECOVER TABLE HR.EMPLOYEES, HR.DEPARTMENTS
  UNTIL TIME "SYSDATE-1/24"
  AUXILIARY DESTINATION '/u01/aux_dest';
```

**Caso D — gerar apenas o dump (sem importar):**
```rman
RECOVER TABLE HR.EMPLOYEES
  UNTIL TIME "SYSDATE-2/24"
  AUXILIARY DESTINATION '/u01/aux_dest'
  DATAPUMP DESTINATION '/u01/dumps'
  DUMP FILE 'employees_recovered.dmp'
  NOTABLEIMPORT;
```

### 4. Acompanhar o progresso

Em outra sessão SQL*Plus:
```sql
SELECT sid, serial#, opname, target, sofar, totalwork,
       ROUND(sofar/totalwork*100, 2) AS pct
FROM   v$session_longops
WHERE  totalwork > 0
AND    sofar <> totalwork;
```

Ou monitorar o alert log:
```bash
tail -f $ORACLE_BASE/diag/rdbms/<db>/<sid>/trace/alert_*.log
```

## Validação

Depois do RECOVER TABLE terminar:

```sql
-- Conferir registros da tabela recuperada
SELECT COUNT(*) FROM hr.employees_recovered;

-- Comparar com tabela atual
SELECT COUNT(*) FROM hr.employees;

-- Validar amostra de dados
SELECT * FROM hr.employees_recovered FETCH FIRST 5 ROWS ONLY;
```

A instância auxiliar deve ter sido removida automaticamente — confirme:
```bash
ls -la /u01/aux_dest
# Deve estar vazio ou com arquivos residuais apenas
ps -ef | grep -i pmon | grep -i aux
# Não deve retornar processos
```

## Troubleshooting

| Erro | Causa provável | Solução |
|------|----------------|---------|
| `RMAN-05055: aux destination not specified` | Faltou cláusula `AUXILIARY DESTINATION` | Adicionar diretório válido |
| `ORA-01017: invalid username/password` durante recovery | Senha do `sys` mudou após o backup | Não é possível usar o backup para PITR antes da mudança; restaurar password file |
| `RMAN-06474: insufficient space in auxiliary destination` | Diretório aux pequeno | Liberar espaço; precisa caber SYSTEM + SYSAUX + UNDO + tablespace alvo |
| `ORA-39083: Object type TABLE failed to create` no import | Tabela já existe no destino sem REMAP | Usar `REMAP TABLE` ou dropar a tabela atual antes |
| Recovery muito lento | Volume de archives a aplicar é alto | Esperado — é o custo do PITR. Usar SCN mais próximo se possível |
| Auxiliary instance ficou órfã após erro | RMAN não conseguiu limpar | Matar manualmente os processos da instância aux e remover arquivos em `/u01/aux_dest` |

## Limpeza manual (se necessário)

```bash
# Identificar SID da instância auxiliar (geralmente começa com a letra do nome do banco)
ps -ef | grep ora_pmon_

# Remover arquivos residuais
rm -rf /u01/aux_dest/*
```

## Boas práticas

- Sempre prefira `REMAP TABLE` em produção: evita sobrescrever a tabela atual e permite comparar versões antes de decidir o que fazer.
- Verifique espaço na auxiliary destination antes — falha de espaço aborta toda a operação.
- Para tabelas com **constraints/dependências**, use `NOTABLEIMPORT` e faça import manual com Data Pump controlando opções.
- Documente o SCN/timestamp alvo antes de rodar — facilita repetir se algo der errado.
