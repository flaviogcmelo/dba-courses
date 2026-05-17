---
name: habilitar-fra
description: Habilitar e configurar a Fast Recovery Area (FRA) em um banco Oracle 19c Single Instance. Use sempre que o desafio envolver configurar área de recuperação rápida, definir db_recovery_file_dest, db_recovery_file_dest_size, ou preparar o ambiente para receber backups RMAN, archived logs e flashback logs. Use também quando o aluno precisar verificar o uso/ocupação da FRA ou redimensioná-la.
---

# Habilitar FRA (Fast Recovery Area)

## Objetivo

Configurar a Fast Recovery Area (FRA) no banco Oracle 19c para centralizar arquivos de recuperação: backups RMAN, archived redo logs, flashback logs, control file autobackups e cópias de control file/online redo logs.

## Pré-requisitos

- Oracle Database 19c Single Instance instalado e operacional
- Acesso `SYSDBA` (usuário `sys`)
- Diretório no sistema operacional com espaço disponível (recomendado: filesystem separado dos datafiles)
- Permissão de escrita do usuário `oracle` no diretório destino

## Passo a passo

### 1. Verificar configuração atual

```sql
SHOW PARAMETER db_recovery_file_dest
SHOW PARAMETER db_recovery_file_dest_size
```

### 2. Criar diretório no sistema operacional (se necessário)

```bash
mkdir -p /u01/app/oracle/fast_recovery_area
chown -R oracle:oinstall /u01/app/oracle/fast_recovery_area
chmod 750 /u01/app/oracle/fast_recovery_area
```

### 3. Definir tamanho da FRA

```sql
ALTER SYSTEM SET db_recovery_file_dest_size = 10G SCOPE=BOTH;
```

> **Importante**: defina o `size` ANTES do `dest`. O Oracle valida o parâmetro de destino contra o tamanho configurado.

### 4. Definir o destino da FRA

```sql
ALTER SYSTEM SET db_recovery_file_dest = '/u01/app/oracle/fast_recovery_area' SCOPE=BOTH;
```

### 5. (Opcional) Configurar retenção de archived logs na FRA

```sql
ALTER SYSTEM SET db_flashback_retention_target = 1440 SCOPE=BOTH;  -- minutos (24h)
```

## Validação

```sql
-- Confirmar parâmetros
SHOW PARAMETER db_recovery_file_dest

-- Verificar uso da FRA
SELECT name,
       space_limit/1024/1024/1024     AS limit_gb,
       space_used/1024/1024/1024      AS used_gb,
       space_reclaimable/1024/1024/1024 AS reclaimable_gb,
       number_of_files
FROM   v$recovery_file_dest;

-- Detalhamento por tipo de arquivo
SELECT file_type,
       percent_space_used,
       percent_space_reclaimable,
       number_of_files
FROM   v$flash_recovery_area_usage;
```

Resultado esperado: parâmetros aparecem com os valores definidos e a view `v$recovery_file_dest` retorna uma linha com o caminho configurado.

## Troubleshooting

| Erro | Causa provável | Solução |
|------|----------------|---------|
| `ORA-19802: cannot use DB_RECOVERY_FILE_DEST without DB_RECOVERY_FILE_DEST_SIZE` | Tentou definir o destino antes do tamanho | Defina `db_recovery_file_dest_size` primeiro |
| `ORA-19816: WARNING: Files may exist...` | Diretório já contém arquivos de outra instância | Limpar diretório ou escolher outro path |
| `ORA-19504: failed to create file` | Permissão insuficiente no SO | Ajustar owner/permissão para `oracle:oinstall` |

## Rollback

```sql
-- Desabilitar a FRA (apenas se necessário)
ALTER SYSTEM SET db_recovery_file_dest = '' SCOPE=BOTH;
ALTER SYSTEM SET db_recovery_file_dest_size = 0 SCOPE=BOTH;
```

> **Atenção**: não desabilite a FRA se já houver archivelogs/backups dependentes dela.
