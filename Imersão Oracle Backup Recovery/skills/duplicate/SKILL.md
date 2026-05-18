---
name: duplicate
description: Duplicar um banco Oracle 19c Single Instance usando RMAN DUPLICATE DATABASE, criando uma cópia em outro servidor ou no mesmo servidor com outro nome, a partir de backup (backup-based) ou diretamente do banco em produção (active duplicate). Use sempre que o desafio envolver clonar banco para ambiente de teste/homologação, criar standby manual, replicar produção em DEV, usar DUPLICATE TARGET DATABASE TO, configurar instância auxiliar, ou converter nomes de datafiles entre servidores.
---

# Duplicate Database (RMAN DUPLICATE)

## Objetivo

Criar uma cópia (clone) de um banco Oracle 19c em outra instância — mesmo servidor com outro nome, ou em outro servidor — útil para ambientes de teste, homologação, refresh de DEV ou criação manual de standby.

## Modalidades

| Modo | Descrição | Quando usar |
|------|-----------|-------------|
| **Backup-based** | Usa backups RMAN existentes | Quando há backups acessíveis e quer poupar a produção |
| **Active duplicate** | Cópia direta do banco em produção via rede | Quando não há backup ou se quer a cópia mais recente |
| **Active sem auxiliary channels** | A partir do 12c, copia direto sem precisar de backup intermediário | Padrão moderno; requer Net listener funcional no target |

## Pré-requisitos

- Oracle 19c instalado no servidor destino (mesmo patch level recomendado)
- Diretórios criados no destino: `admin`, `audit`, datafiles, `fast_recovery_area`
- Listener configurado no destino com entrada **estática** para o banco auxiliar (importante porque o banco ainda não existe para registrar dinamicamente)
- **Password file** no destino com a senha do `sys` igual à do source
- Para backup-based: backups acessíveis pelo destino (mesmo path ou via NFS)
- Para active duplicate: conectividade TNS bidirecional entre source e destino
- Acesso `SYSDBA` em ambos

## Convenções deste exemplo

- Source: `PROD` em servidor `srv-prod`
- Auxiliary (clone): `DUPDB` em servidor `srv-dup`

## Passo a passo — Active Duplicate (recomendado)

### 1. Preparar o servidor destino

```bash
# Criar diretórios
mkdir -p /u01/app/oracle/admin/DUPDB/{adump,dpdump}
mkdir -p /u01/app/oracle/oradata/DUPDB
mkdir -p /u01/app/oracle/fast_recovery_area/DUPDB
```

### 2. Criar pfile inicial mínimo no destino

`$ORACLE_HOME/dbs/initDUPDB.ora`:
```
DB_NAME=DUPDB
DB_UNIQUE_NAME=DUPDB
DB_BLOCK_SIZE=8192
SGA_TARGET=2G
PGA_AGGREGATE_TARGET=512M
CONTROL_FILES='/u01/app/oracle/oradata/DUPDB/control01.ctl'
DB_RECOVERY_FILE_DEST='/u01/app/oracle/fast_recovery_area'
DB_RECOVERY_FILE_DEST_SIZE=20G
DIAGNOSTIC_DEST='/u01/app/oracle'
REMOTE_LOGIN_PASSWORDFILE=EXCLUSIVE
```

### 3. Criar password file no destino

```bash
orapwd file=$ORACLE_HOME/dbs/orapwDUPDB password=<senha_sys_do_source> format=12
```

> A senha **deve ser idêntica** à do `sys` no source.

### 4. Configurar listener estático no destino

`$ORACLE_HOME/network/admin/listener.ora`:
```
SID_LIST_LISTENER =
  (SID_LIST =
    (SID_DESC =
      (GLOBAL_DBNAME = DUPDB)
      (ORACLE_HOME = /u01/app/oracle/product/19c/dbhome_1)
      (SID_NAME = DUPDB)
    )
  )
```

Reiniciar listener:
```bash
lsnrctl stop && lsnrctl start
```

### 5. Configurar tnsnames em ambos os servidores

`$ORACLE_HOME/network/admin/tnsnames.ora`:
```
PROD =
  (DESCRIPTION =
    (ADDRESS = (PROTOCOL = TCP)(HOST = srv-prod)(PORT = 1521))
    (CONNECT_DATA = (SERVICE_NAME = PROD))
  )

DUPDB =
  (DESCRIPTION =
    (ADDRESS = (PROTOCOL = TCP)(HOST = srv-dup)(PORT = 1521))
    (CONNECT_DATA = (SID = DUPDB) (UR=A))
  )
```

> `(UR=A)` permite conectar mesmo que o banco esteja só em NOMOUNT.

### 6. Startar a auxiliary em NOMOUNT

```bash
export ORACLE_SID=DUPDB
sqlplus / as sysdba
```
```sql
STARTUP NOMOUNT PFILE='?/dbs/initDUPDB.ora';
```

### 7. Testar conectividade

A partir do servidor destino:
```bash
sqlplus sys/<senha>@PROD as sysdba
sqlplus sys/<senha>@DUPDB as sysdba
```

Ambas conexões precisam funcionar.

### 8. Executar o DUPLICATE

Conectar no RMAN a partir do servidor destino:
```bash
rman target sys/<senha>@PROD auxiliary sys/<senha>@DUPDB
```

Executar o duplicate active:
```rman
RUN {
  ALLOCATE AUXILIARY CHANNEL aux1 DEVICE TYPE DISK;
  ALLOCATE AUXILIARY CHANNEL aux2 DEVICE TYPE DISK;
  DUPLICATE TARGET DATABASE TO DUPDB
    FROM ACTIVE DATABASE
    SPFILE
      SET DB_FILE_NAME_CONVERT='/u01/app/oracle/oradata/PROD','/u01/app/oracle/oradata/DUPDB'
      SET LOG_FILE_NAME_CONVERT='/u01/app/oracle/oradata/PROD','/u01/app/oracle/oradata/DUPDB'
      SET DB_RECOVERY_FILE_DEST='/u01/app/oracle/fast_recovery_area'
      SET DB_UNIQUE_NAME='DUPDB'
      SET CONTROL_FILES='/u01/app/oracle/oradata/DUPDB/control01.ctl','/u01/app/oracle/oradata/DUPDB/control02.ctl'
    NOFILENAMECHECK;
}
```

## Passo a passo — Backup-Based Duplicate

Idêntico aos passos 1-7, mas o backup do source precisa estar acessível ao destino (mesmo path ou NFS).

```bash
rman auxiliary sys/<senha>@DUPDB
```
```rman
DUPLICATE DATABASE TO DUPDB
  BACKUP LOCATION '/u01/backup/PROD'
  SPFILE
    SET DB_FILE_NAME_CONVERT='/u01/app/oracle/oradata/PROD','/u01/app/oracle/oradata/DUPDB'
    SET LOG_FILE_NAME_CONVERT='/u01/app/oracle/oradata/PROD','/u01/app/oracle/oradata/DUPDB'
  NOFILENAMECHECK;
```

> No backup-based, não é necessário conectar no `TARGET` — basta o `AUXILIARY` e indicar o `BACKUP LOCATION`.

## Validação

No banco clone:
```sql
SELECT name, db_unique_name, open_mode FROM v$database;
-- name=DUPDB, open_mode=READ WRITE

SELECT instance_name, status FROM v$instance;

SELECT file_name FROM dba_data_files;
-- Paths devem refletir o destino, não o source

-- DBID deve ser diferente do source
SELECT dbid FROM v$database;
```

Teste funcional:
```sql
SELECT count(*) FROM dba_objects;
ALTER SYSTEM SWITCH LOGFILE;
```

## Troubleshooting

| Erro | Causa provável | Solução |
|------|----------------|---------|
| `ORA-12528: TNS:listener: all appropriate instances are blocking new connections` | Listener sem entrada estática para o auxiliary | Adicionar `SID_LIST` no listener.ora e reiniciar |
| `ORA-01017: invalid username/password; logon denied` na conexão auxiliary | Password file ausente ou senha diferente do source | Recriar `orapw<SID>` com a mesma senha |
| `RMAN-05541: no archived logs found` | Active duplicate sem backups e poucos archives | Forçar log switch no source antes; ou usar `NOREDO` para dups inconsistentes |
| `RMAN-05001: auxiliary file name conflicts with target file name` | `*_CONVERT` ausente ou mal definido com source/destino no mesmo servidor | Definir corretamente `DB_FILE_NAME_CONVERT` e `LOG_FILE_NAME_CONVERT` |
| Duplicate trava em `RESTORE` | Backup-based sem acesso aos arquivos pelo destino | Conferir NFS/permissão; usar `BACKUP LOCATION` com caminho acessível |
| `ORA-19505: failed to identify file` | Path do backup não existe no destino | Copiar backupsets para path local ou montar NFS |

## Pós-duplicate (recomendado)

```sql
-- Alterar passwords de usuários sensíveis (já que vieram da prod)
ALTER USER hr IDENTIFIED BY <nova_senha>;

-- Recriar/registrar jobs do scheduler conforme o ambiente
-- Ajustar dblinks que apontem para outros ambientes
SELECT db_link FROM dba_db_links;

-- Desativar jobs sensíveis se for ambiente de teste
EXEC DBMS_SCHEDULER.disable('NOME_JOB');
```

```rman
-- Configurar retenção do novo banco
CONFIGURE RETENTION POLICY TO RECOVERY WINDOW OF 7 DAYS;
BACKUP DATABASE PLUS ARCHIVELOG;
```
