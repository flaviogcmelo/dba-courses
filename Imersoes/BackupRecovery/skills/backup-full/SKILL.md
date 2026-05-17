---
name: backup-full
description: Executar backup full de um banco Oracle 19c Single Instance usando RMAN, incluindo datafiles, controlfile, spfile e archived redo logs. Use sempre que o desafio envolver criar backup completo (BACKUP DATABASE), configurar parâmetros de retenção do RMAN, validar integridade de backup, configurar autobackup do controlfile, ou listar/relatórios de backupsets existentes.
---

# Backup Full com RMAN

## Objetivo

Executar um backup full do banco Oracle 19c usando RMAN, cobrindo datafiles, controlfile, spfile e archived redo logs — base para qualquer estratégia de recovery.

## Pré-requisitos

- Banco em modo **ARCHIVELOG** (skill `habilitar-archivelog`)
- **FRA configurada** (skill `habilitar-fra`) ou destino de backup definido manualmente
- Acesso `SYSDBA` ou usuário com role `SYSBACKUP`
- Espaço em disco suficiente: tamanho aproximado dos datafiles em uso (não do tamanho alocado)

## Passo a passo

### 1. Conectar no RMAN

```bash
rman target /
```

Ou conectando explicitamente:
```bash
rman target sys/senha@nome_servico
```

### 2. Configurar parâmetros persistentes (uma única vez)

```rman
-- Política de retenção (manter recuperabilidade dos últimos N dias)
CONFIGURE RETENTION POLICY TO RECOVERY WINDOW OF 7 DAYS;

-- Autobackup do controlfile e spfile a cada backup
CONFIGURE CONTROLFILE AUTOBACKUP ON;

-- Destino do autobackup (se quiser fora da FRA)
CONFIGURE CONTROLFILE AUTOBACKUP FORMAT FOR DEVICE TYPE DISK TO '/u01/backup/cf_%F';

-- Paralelismo
CONFIGURE DEVICE TYPE DISK PARALLELISM 2 BACKUP TYPE TO BACKUPSET;

-- Verificar configuração
SHOW ALL;
```

### 3. Executar o backup full

**Opção A — Backup simples para FRA:**
```rman
BACKUP DATABASE PLUS ARCHIVELOG;
```

**Opção B — Backup com tag e destino explícito:**
```rman
RUN {
  ALLOCATE CHANNEL c1 DEVICE TYPE DISK FORMAT '/u01/backup/df_%U';
  ALLOCATE CHANNEL c2 DEVICE TYPE DISK FORMAT '/u01/backup/df_%U';
  BACKUP
    TAG 'FULL_DAILY'
    DATABASE
    PLUS ARCHIVELOG;
  RELEASE CHANNEL c1;
  RELEASE CHANNEL c2;
}
```

**Opção C — Backup com deleção dos archivelogs após backup:**
```rman
BACKUP DATABASE PLUS ARCHIVELOG DELETE INPUT;
```

### 4. Verificar integridade do backup

```rman
BACKUP VALIDATE DATABASE;
RESTORE DATABASE VALIDATE;
```

> `RESTORE ... VALIDATE` simula o restore sem alterar arquivos — confirma que os backupsets estão íntegros e completos.

## Validação

```rman
-- Listar backups
LIST BACKUP SUMMARY;
LIST BACKUP OF DATABASE;
LIST BACKUP OF ARCHIVELOG ALL;

-- Detalhes
LIST BACKUP BY FILE;

-- Relatório de recuperabilidade
REPORT NEED BACKUP;
REPORT OBSOLETE;
REPORT SCHEMA;
```

Em SQL*Plus:
```sql
SELECT session_recid, status, start_time, end_time,
       input_bytes_display, output_bytes_display
FROM   v$rman_backup_job_details
ORDER  BY start_time DESC
FETCH  FIRST 5 ROWS ONLY;
```

## Troubleshooting

| Erro | Causa provável | Solução |
|------|----------------|---------|
| `RMAN-06059: expected archived log not found` | Archive perdido entre dois backups | `CROSSCHECK ARCHIVELOG ALL;` seguido de `DELETE EXPIRED ARCHIVELOG ALL;` |
| `ORA-19809: limit exceeded for recovery files` | FRA cheia | Aumentar `db_recovery_file_dest_size` ou rodar `DELETE OBSOLETE` |
| `RMAN-03009: failure of backup command` + `ORA-19502: write error` | Disco cheio ou sem permissão no FORMAT path | Liberar espaço ou ajustar permissão do diretório |
| Backup muito lento | Sem paralelismo | `CONFIGURE DEVICE TYPE DISK PARALLELISM N` (N = nº de CPUs/2) |

## Manutenção

```rman
-- Validar consistência entre catálogo e arquivos físicos
CROSSCHECK BACKUP;
CROSSCHECK ARCHIVELOG ALL;

-- Remover backups que violam a política de retenção
DELETE OBSOLETE;

-- Remover registros de backups inexistentes no disco
DELETE EXPIRED BACKUP;
```
