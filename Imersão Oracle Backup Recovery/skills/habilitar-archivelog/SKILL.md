---
name: habilitar-archivelog
description: Habilitar o modo ARCHIVELOG em um banco Oracle 19c Single Instance, pré-requisito para backups online (hot backup), Data Guard, Flashback Database e recoveries point-in-time. Use sempre que o desafio envolver mudar o banco para archivelog mode, configurar log_archive_dest_n, verificar status de archiving, forçar switch de redo log ou validar geração de archived redo logs.
---

# Habilitar Archivelog

## Objetivo

Colocar o banco Oracle 19c em modo ARCHIVELOG, permitindo:
- Backups RMAN online (hot backup) com o banco em produção
- Recovery point-in-time (PITR)
- Configuração de Flashback Database
- Configuração futura de Data Guard

## Pré-requisitos

- Banco Oracle 19c Single Instance operacional
- Acesso `SYSDBA`
- **FRA habilitada** (skill `habilitar-fra`) ou `log_archive_dest_1` definido manualmente
- Janela de manutenção: o banco precisa ser **reiniciado em mount** para alterar o modo

## Passo a passo

### 1. Verificar modo atual

```sql
SELECT log_mode FROM v$database;
ARCHIVE LOG LIST;
```

Saída esperada (banco em NOARCHIVELOG):
```
Database log mode              No Archive Mode
Automatic archival             Disabled
```

### 2. (Opcional) Definir destino de archive fora da FRA

Se NÃO estiver usando FRA, configure um destino explícito:

```sql
ALTER SYSTEM SET log_archive_dest_1 = 'LOCATION=/u01/app/oracle/archive' SCOPE=BOTH;
ALTER SYSTEM SET log_archive_format = '%t_%s_%r.arc' SCOPE=SPFILE;
```

> Se a FRA está habilitada, o Oracle usa automaticamente `USE_DB_RECOVERY_FILE_DEST`.

### 3. Shutdown limpo do banco

```sql
SHUTDOWN IMMEDIATE;
```

### 4. Startup em modo MOUNT

```sql
STARTUP MOUNT;
```

### 5. Alterar para modo ARCHIVELOG

```sql
ALTER DATABASE ARCHIVELOG;
```

### 6. Abrir o banco

```sql
ALTER DATABASE OPEN;
```

### 7. Forçar um switch para gerar o primeiro archive

```sql
ALTER SYSTEM SWITCH LOGFILE;
ALTER SYSTEM ARCHIVE LOG CURRENT;
```

## Validação

```sql
-- Confirmar modo
SELECT log_mode FROM v$database;
-- Esperado: ARCHIVELOG

-- Resumo do archive
ARCHIVE LOG LIST;

-- Verificar archives gerados
SELECT name, sequence#, first_time, completion_time
FROM   v$archived_log
ORDER  BY completion_time DESC
FETCH  FIRST 5 ROWS ONLY;

-- Destino e status
SELECT dest_id, status, destination
FROM   v$archive_dest
WHERE  status = 'VALID';
```

## Troubleshooting

| Erro | Causa provável | Solução |
|------|----------------|---------|
| `ORA-01126: database must be mounted in this instance and not open` | Banco está OPEN ao tentar `ALTER DATABASE ARCHIVELOG` | Fazer SHUTDOWN IMMEDIATE e STARTUP MOUNT |
| `ORA-19809: limit exceeded for recovery files` | FRA cheia | Aumentar `db_recovery_file_dest_size` ou limpar archives antigos via RMAN |
| `ORA-16019: cannot use LOG_ARCHIVE_DEST_1 with LOG_ARCHIVE_DEST` | Conflito entre parâmetros legados | Limpar `log_archive_dest` antigo (`ALTER SYSTEM RESET log_archive_dest`) |
| Archive não é gerado após switch | Processo ARCn travado | Verificar `v$archive_processes`; reiniciar com `ALTER SYSTEM ARCHIVE LOG START` |

## Rollback (voltar para NOARCHIVELOG)

```sql
SHUTDOWN IMMEDIATE;
STARTUP MOUNT;
ALTER DATABASE NOARCHIVELOG;
ALTER DATABASE OPEN;
```

> **Atenção**: voltar para NOARCHIVELOG invalida backups online existentes e impede recovery point-in-time.
