---
name: configure-flashback
description: Habilitar e configurar o Flashback Database em um banco Oracle 19c Single Instance, permitindo reverter o banco inteiro para um ponto no tempo anterior sem necessidade de restore de backup. Use sempre que o desafio envolver ativar flashback database, configurar db_flashback_retention_target, criar/usar restore points (garantidos ou normais), executar FLASHBACK DATABASE TO, ou verificar flashback logs e janela de retenção disponível.
---

# Configure Flashback Database

## Objetivo

Habilitar o Flashback Database para permitir reverter o banco inteiro para um ponto no tempo passado (SCN, timestamp ou restore point) sem realizar restore de backup — ideal para reverter operações errôneas em janelas de teste, deploys ou treinamentos.

## Pré-requisitos

- Banco em modo **ARCHIVELOG** (skill `habilitar-archivelog`)
- **FRA habilitada** (skill `habilitar-fra`) com espaço suficiente para flashback logs
- Acesso `SYSDBA`
- Recomendado: filesystem com ~30% de overhead sobre o tamanho do banco para acomodar flashback logs

## Passo a passo

### 1. Verificar status atual

```sql
SELECT flashback_on FROM v$database;
SHOW PARAMETER db_flashback_retention_target
```

### 2. Definir janela de retenção (em minutos)

```sql
-- 1440 minutos = 24 horas
ALTER SYSTEM SET db_flashback_retention_target = 1440 SCOPE=BOTH;
```

### 3. Habilitar Flashback Database

A partir do 12c, isso pode ser feito com o banco OPEN:

```sql
ALTER DATABASE FLASHBACK ON;
```

> Em ambientes legados ou se houver erro, o procedimento clássico é:
> ```sql
> SHUTDOWN IMMEDIATE;
> STARTUP MOUNT;
> ALTER DATABASE FLASHBACK ON;
> ALTER DATABASE OPEN;
> ```

### 4. (Opcional) Criar Guaranteed Restore Point

Útil antes de testes ou deploys. Garante que o banco pode voltar exatamente àquele ponto, **independente** da `db_flashback_retention_target`:

```sql
CREATE RESTORE POINT antes_do_deploy GUARANTEE FLASHBACK DATABASE;
```

Restore point normal (não garantido):
```sql
CREATE RESTORE POINT marco_teste;
```

### 5. Exemplo de uso — flashback para um restore point

```sql
-- 1. Listar restore points disponíveis
SELECT name, scn, time, guarantee_flashback_database
FROM   v$restore_point;

-- 2. Executar o flashback (banco precisa estar em MOUNT)
SHUTDOWN IMMEDIATE;
STARTUP MOUNT;
FLASHBACK DATABASE TO RESTORE POINT antes_do_deploy;

-- 3. Abrir com RESETLOGS
ALTER DATABASE OPEN RESETLOGS;
```

## Validação

```sql
-- Confirmar flashback habilitado
SELECT flashback_on FROM v$database;
-- Esperado: YES

-- Janela de flashback disponível
SELECT oldest_flashback_scn,
       oldest_flashback_time,
       retention_target,
       flashback_size/1024/1024 AS flashback_size_mb
FROM   v$flashback_database_log;

-- Restore points
SELECT name, scn, time, guarantee_flashback_database, storage_size/1024/1024 AS size_mb
FROM   v$restore_point;

-- Uso da FRA por flashback logs
SELECT file_type, percent_space_used
FROM   v$flash_recovery_area_usage
WHERE  file_type = 'FLASHBACK LOG';
```

## Troubleshooting

| Erro | Causa provável | Solução |
|------|----------------|---------|
| `ORA-38706: Cannot turn on FLASHBACK DATABASE logging` | Banco em NOARCHIVELOG | Habilitar ARCHIVELOG primeiro |
| `ORA-38760: This database instance failed to turn on flashback database` | FRA não configurada | Configurar `db_recovery_file_dest` e size |
| `ORA-38729: Not enough flashback database log data to do FLASHBACK` | Janela de retenção menor que o tempo solicitado | Usar guaranteed restore point ou restore via RMAN |
| FRA enchendo rapidamente | Flashback logs ocupando espaço + guaranteed restore point | Reduzir retention, dropar restore points antigos, ou aumentar FRA |

## Rollback / Limpeza

```sql
-- Remover um restore point
DROP RESTORE POINT antes_do_deploy;

-- Desabilitar flashback database
ALTER DATABASE FLASHBACK OFF;
```

> **Atenção**: ao desabilitar flashback, todos os flashback logs são descartados. Drop em guaranteed restore points libera espaço significativo na FRA.
