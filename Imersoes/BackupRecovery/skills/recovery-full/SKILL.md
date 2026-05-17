---
name: recovery-full
description: Executar restore e recovery completo de um banco Oracle 19c Single Instance a partir de backup RMAN, incluindo perda total de datafiles ou do controlfile. Use sempre que o desafio envolver RESTORE DATABASE, RECOVER DATABASE, recovery completo, recovery até o último archivelog disponível, ou simular crash recovery após perda de arquivos físicos do banco.
---

# Recovery Full (restore + recover completo)

## Objetivo

Restaurar e recuperar o banco Oracle 19c por completo a partir de um backup RMAN — cenário típico: perda de datafiles, perda do controlfile, ou desastre que exige reconstrução do banco.

## Pré-requisitos

- Backup RMAN válido (skill `backup-full` ou `backup-compress` executada)
- Banco em modo **ARCHIVELOG** (skill `habilitar-archivelog`)
- Archived redo logs disponíveis (no disco ou backupados)
- Acesso `SYSDBA`
- **Importante**: se o controlfile foi perdido, é necessário o **DBID** do banco original

## Diagnóstico inicial (executar sempre primeiro)

Antes de escolher o cenário, colete o estado real do ambiente:

### 1. Verificar o alertlog

```bash
# Localizar e exibir as últimas 150 linhas do alertlog
ALERTLOG=$(find /u01/app/oracle/diag/rdbms -name "alert_${ORACLE_SID}.log" 2>/dev/null | head -1)
tail -150 $ALERTLOG | grep -E "ORA-|Error|error|MISSING|missing|No such file|Cannot|cannot|WARNING|Checker run"
```

Erros relevantes a procurar:
- `ORA-01110` + `ORA-01565` + `No such file` → datafile ausente no disco
- `ORA-00313` / `ORA-00312` → redo log inacessível
- `ORA-00205` → controlfile inacessível
- `Checker run found N new persistent data failures` → falhas persistentes detectadas

### 2. Confirmar arquivos ausentes no disco

```bash
# Verificar se os datafiles reportados no alertlog existem fisicamente
ls -lh /u02/oradata/${ORACLE_SID}/system01.dbf
ls -lh /u02/oradata/${ORACLE_SID}/sysaux01.dbf
ls -lh /u02/oradata/${ORACLE_SID}/undotbs01.dbf
ls -lh /u02/oradata/${ORACLE_SID}/users01.dbf

# Listar tudo que existe no diretório de dados
ls -lh /u02/oradata/${ORACLE_SID}/
```

### 3. Verificar estado da instância e backups

```bash
# Estado da instância
sqlplus -s / as sysdba <<EOF
SELECT instance_name, status, database_status FROM v\$instance;
SELECT name, open_mode, log_mode FROM v\$database;
SELECT file#, name, status FROM v\$datafile;
SELECT * FROM v\$recover_file;
EOF
```

```bash
# Backups disponíveis no RMAN
rman target / <<EOF
LIST BACKUP SUMMARY;
SHOW ALL;
EOF
```

### 4. Determinar o cenário

| Controlfile | Datafiles CDB | Cenário |
|-------------|--------------|---------|
| OK | Alguns ausentes | Cenário 1 — restore por datafile |
| OK | Todos ausentes | Cenário 2 — restore completo |
| Ausente | Qualquer | Cenário 3 — restore controlfile + banco |

---

## Cenários cobertos

1. **Recovery completo até o momento atual** — perda de datafile com banco e controlfile íntegros
2. **Recovery completo com perda de controlfile** — restore do controlfile a partir do autobackup
3. **Recovery completo com perda total** — reconstrução do banco do zero

## Cenário 1 — Perda de datafile (banco e controlfile íntegros)

### 1. Identificar o problema
```sql
SELECT name, status FROM v$datafile WHERE status = 'OFFLINE';
SELECT * FROM v$recover_file;
```

### 2. Colocar o datafile offline (se ainda não estiver)
```sql
ALTER DATABASE DATAFILE 5 OFFLINE;
```

### 3. Restore e recover no RMAN
```rman
RUN {
  RESTORE DATAFILE 5;
  RECOVER DATAFILE 5;
  SQL "ALTER DATABASE DATAFILE 5 ONLINE";
}
```

## Cenário 2 — Perda completa de datafiles (controlfile OK)

```rman
-- Banco precisa estar em MOUNT
SHUTDOWN ABORT;
STARTUP MOUNT;

RESTORE DATABASE;
RECOVER DATABASE;
ALTER DATABASE OPEN;
```

## Cenário 3 — Perda de controlfile (com autobackup configurado)

```bash
rman target /
```

```rman
-- 1. Configurar DBID (obrigatório quando spfile/controlfile foram perdidos)
SET DBID 1234567890;

-- 2. Startup nomount (sem spfile, RMAN sobe um dummy)
STARTUP NOMOUNT;

-- 3. Restore do spfile a partir do autobackup
RESTORE SPFILE FROM AUTOBACKUP;

-- 4. Restart com spfile correto
SHUTDOWN IMMEDIATE;
STARTUP NOMOUNT;

-- 5. Restore do controlfile
RESTORE CONTROLFILE FROM AUTOBACKUP;

-- 6. Mount
ALTER DATABASE MOUNT;

-- 7. Validar catálogo
CROSSCHECK BACKUP;
CROSSCHECK ARCHIVELOG ALL;

-- 8. Restore + recover
RESTORE DATABASE;
RECOVER DATABASE;

-- 9. Abrir com RESETLOGS (obrigatório quando o controlfile foi restaurado)
ALTER DATABASE OPEN RESETLOGS;
```

> **Como descobrir o DBID** antes da perda? Guarde com:
> ```sql
> SELECT dbid FROM v$database;
> ```
> Ou recupere do nome do arquivo de autobackup: `c-<DBID>-YYYYMMDD-NN`.

## Validação

```sql
-- Status do banco
SELECT status, open_mode FROM v$instance;
SELECT name, open_mode, log_mode FROM v$database;

-- Datafiles online
SELECT file#, name, status FROM v$datafile;

-- Nenhum datafile precisa de recovery
SELECT * FROM v$recover_file;
-- Esperado: 0 linhas

-- Histórico do recovery
SELECT recid, action, status, start_time, completion_time
FROM   v$rman_status
ORDER  BY start_time DESC
FETCH  FIRST 10 ROWS ONLY;
```

Teste funcional após open:
```sql
ALTER SYSTEM SWITCH LOGFILE;
SELECT count(*) FROM dba_objects;
```

## Troubleshooting

| Erro | Causa provável | Solução |
|------|----------------|---------|
| `RMAN-06054: media recovery requesting unknown archived log` | Archive necessário não está disponível | Restore do archive via `RESTORE ARCHIVELOG`; se não houver backup, recovery incompleto será necessário (próxima skill) |
| `ORA-01113: file N needs media recovery` | Datafile inconsistente após restore | Executar `RECOVER DATAFILE N` ou `RECOVER DATABASE` |
| `ORA-01194: file 1 needs more recovery to be consistent` | Tentou abrir o banco antes do recovery completar | Rodar `RECOVER DATABASE` até "Media recovery complete" |
| `RMAN-06172: no autobackup found` | Autobackup não estava configurado ou foi perdido | Procurar manualmente: `RESTORE CONTROLFILE FROM '/path/to/c-...'` |
| Após open, alertas sobre tempfile | Tempfiles não são restaurados | Recriar: `ALTER TABLESPACE TEMP ADD TEMPFILE '...' SIZE Xg;` |

## Pós-recovery (recomendado)

```rman
-- Fazer backup full novo (RESETLOGS invalidou backups anteriores no cenário 3)
BACKUP DATABASE PLUS ARCHIVELOG;
```
