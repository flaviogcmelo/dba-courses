# Oracle Database 19c Enterprise Edition
## Guia Completo de Instalação — Oracle Linux 8.x / VirtualBox (x86-64)

**Versão do documento:** 1.0  
**Data:** 2026-05-16  
**Autor:** DBA Oracle — Imersão Backup & Recovery  
**Classificação:** Material de Treinamento  

---

## 1. Descrição do Ambiente Documentado

Este guia documenta a instalação completa e automatizada do **Oracle Database 19c Enterprise Edition (19.3.0)** em uma máquina virtual Oracle Linux 8.x rodando no VirtualBox no Windows 11 (x86-64). O objetivo é reproduzir um ambiente de laboratório equivalente ao ambiente de produção para estudos de **Backup & Recovery**, RMAN, Data Guard e tuning.

### Arquitetura do Ambiente

```
┌─────────────────────────────────────────────────────────────┐
│  Windows 11 Pro x86-64 (Host)                               │
│  RAM: 16 GB+  │  Disco: 500 GB+  │  CPU: Intel/AMD 64-bit  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  VirtualBox 7.x                                     │    │
│  │                                                     │    │
│  │  ┌────────────────────────────────────────────┐     │    │
│  │  │  VM: ol8-dba.localdomain                   │     │    │
│  │  │  OS: Oracle Linux 8.10 (x86-64)            │     │    │
│  │  │  vCPU: 2+  │  RAM: 4 GB+  │  Disco: 50 GB │     │    │
│  │  │  IP:   192.168.56.101 (Host-Only)          │     │    │
│  │  │  GW:   192.168.56.1                        │     │    │
│  │  │                                            │     │    │
│  │  │  Oracle Database 19c EE                    │     │    │
│  │  │  SID: orcl  │  PDB: orclpdb               │     │    │
│  │  └────────────────────────────────────────────┘     │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Pré-requisitos de Hardware e Software

### 2.1 Hardware (Host Windows)

| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| CPU | 4 cores (com VT-x/AMD-V) | 8 cores |
| RAM | 8 GB | 16 GB |
| Disco livre | 80 GB | 200 GB (SSD) |
| Rede | Placa física para NAT | — |

### 2.2 Hardware (VM Oracle Linux)

| Recurso | Mínimo | Configurado |
|---------|--------|-------------|
| vCPU | 2 | 2 |
| RAM | 4 GB | 4 GB |
| Disco Sistema | 30 GB | 50 GB |
| Disco Oracle Data | 20 GB | 50 GB |
| Swap | 4 GB | 4 GB |

### 2.3 Software — Versões Exatas Utilizadas

| Software | Versão | Observação |
|----------|--------|------------|
| Windows 11 | 23H2 (Build 22631) | Host |
| VirtualBox | 7.0.x | Hypervisor |
| Oracle Linux | 8.10 (kernel 5.15.x) | Guest OS |
| Oracle Database | 19.3.0.0.0 (19c) | Target |
| Python | 3.11+ | Para script de automação |
| Paramiko | 3.x | Biblioteca SSH Python |

---

## 3. Downloads Necessários

### 3.1 Oracle Database 19c

| Item | URL | Arquivo |
|------|-----|---------|
| Oracle DB 19c Linux x86-64 | https://www.oracle.com/database/technologies/oracle19c-linux-downloads.html | `V982063-01-DB-193000-x86-64.zip` (~3 GB) |

> **Nota:** É necessário uma conta gratuita em https://edelivery.oracle.com ou https://support.oracle.com para baixar o instalador.

### 3.2 Oracle Linux 8

| Item | URL |
|------|-----|
| ISO Oracle Linux 8.x | https://yum.oracle.com/oracle-linux-isos.html |
| UEK Kernel (já incluso) | https://yum.oracle.com/ |

### 3.3 VirtualBox

| Item | URL |
|------|-----|
| VirtualBox 7.x | https://www.virtualbox.org/wiki/Downloads |
| Extension Pack | https://www.virtualbox.org/wiki/Downloads |

### 3.4 Python e Paramiko (Script de Automação)

```powershell
# Instalar Python 3.11+
winget install Python.Python.3.11

# Instalar Paramiko
pip install paramiko
```

---

## 4. Criação e Configuração da VM no VirtualBox

### 4.1 Criar a Máquina Virtual

No VirtualBox Manager, clique em **New** e configure:

```
Nome        : ol8-dba
Pasta       : C:\VMs\  (ou outro local com espaço)
Tipo        : Linux
Versão      : Oracle Linux 8.x (64-bit)
RAM         : 4096 MB
CPU         : 2 vCPUs
HDD         : 50 GB  (VDI, dynamically allocated)
```

### 4.2 Configurar Rede (Obrigatório)

A VM precisa de **duas interfaces de rede**:

- **Adaptador 1 (NAT):** para acesso à internet e dnf/yum
- **Adaptador 2 (Host-Only):** para conexão SSH do host Windows

```
Settings → Network → Adapter 1: NAT
Settings → Network → Adapter 2: Host-Only Adapter
  Selecione: VirtualBox Host-Only Ethernet Adapter
  IP do host: 192.168.56.1
  DHCP range: 192.168.56.100–200
```

### 4.3 Configurar o Disco de Dados

Adicione um segundo disco virtual para os datafiles Oracle:

```
Settings → Storage → Add Hard Disk
  Tamanho: 50 GB
  Tipo: VDI (Dynamic)
  Nome: ol8-dba-data.vdi
```

Dentro do Linux, este disco aparecerá como `/dev/sdb`.

### 4.4 Configurar CPU e Recursos

```
Settings → System → Processor:
  Processors: 2
  [x] Enable PAE/NX
  [x] Enable VT-x/AMD-V Nested

Settings → Display → Screen:
  Video Memory: 16 MB
```

---

## 5. Instalação do Oracle Linux 8

### 5.1 Boot e Idioma

1. Monte a ISO em **Settings → Storage → Optical Drive**
2. Inicie a VM e pressione Enter em "Install Oracle Linux 8.x"
3. Selecione idioma: **English (United States)**

### 5.2 Particionamento Manual

Recomendado o seguinte esquema de particionamento para o disco de sistema (`/dev/sda`):

| Ponto de Montagem | Tamanho | Tipo | Observação |
|-------------------|---------|------|------------|
| `/boot` | 1 GB | xfs | Boot loader |
| `/boot/efi` | 600 MB | vfat | UEFI |
| `swap` | 4 GB | swap | Obrigatório para Oracle |
| `/` | restante | xfs | Root |

> O disco de dados (`/dev/sdb`) será particionado e formatado posteriormente via script para montar em `/u02`.

### 5.3 Seleção de Software

Em **Software Selection**, escolha:

```
Base Environment: Server
Add-Ons:
  [x] Development Tools
  [x] System Tools
```

### 5.4 Configurações de Rede e Hostname

```
Network & Host Name:
  Interface eth0 (NAT): ON  → obtém IP via DHCP
  Interface eth1 (Host-Only): configurar estático
    IP: 192.168.56.101
    Mask: 255.255.255.0
    GW: (vazio para host-only)
  Hostname: ol8-dba.localdomain
```

### 5.5 Senhas e Usuário

```
Root Password: Welcome#
Create User:   oracle / Oracle19c#
  [x] Make this user administrator
```

### 5.6 Finalização

Clique em **Begin Installation** e aguarde (10–20 min). Ao final, clique em **Reboot**.

---

## 6. Automação via Script Python

### 6.1 Visão Geral

O script `oracle19c_autoinstall.py` executa todas as etapas via SSH usando a biblioteca `paramiko`. Ele autentica preferencialmente com a chave SSH `~/.ssh/id_ed25519` e faz fallback para senha.

### 6.2 Pré-requisitos do Script

```powershell
# Instalar dependência
pip install paramiko

# Verificar conectividade
ping 192.168.56.101

# Testar SSH manualmente (opcional)
ssh -i C:\Users\Flavio.Melo\.ssh\id_ed25519 root@192.168.56.101
```

### 6.3 Executar o Script

```powershell
cd "D:\work\dba-courses\Imersoes\BackupRecovery\Imersão Oracle Backup Recovery"
python oracle19c_autoinstall.py
```

A execução total leva entre **60 e 90 minutos** (maior parte na instalação do software e criação do banco).

---

## 7. Comandos de Preparação do Linux (Ordem de Execução)

Estes são os comandos exatos executados pelo script, com explicação de cada um:

### 7.1 Configuração de Hosts e Hostname

```bash
# Adiciona entrada no /etc/hosts para resolução local do hostname
echo "192.168.56.101  ol8-dba.localdomain  ol8-dba" >> /etc/hosts

# Define o hostname permanentemente (persiste após reboot)
hostnamectl set-hostname ol8-dba.localdomain
```

**Por quê:** O Oracle verifica a resolução reversa do hostname durante a instalação. Sem essa entrada, o pré-requisito de DNS pode falhar.

### 7.2 Pacote de Pré-instalação Oracle

```bash
# Instala o pacote que configura automaticamente:
# - Parâmetros de kernel (/etc/sysctl.d/99-oracle.conf)
# - Limites de sistema (/etc/security/limits.d/oracle.conf)
# - Usuário oracle com grupos corretos (oinstall, dba, oper, backupdba, dgdba, kmdba, racdba)
# - Dependências de SO necessárias (binutils, glibc, libaio, etc.)
dnf install -y oracle-database-preinstall-19c
```

**Por quê:** Substituí manualmente a configuração de dezenas de parâmetros de kernel e de SO. A Oracle disponibiliza esse pacote exatamente para isso, eliminando erros humanos.

Parâmetros de kernel configurados automaticamente:

```ini
# /etc/sysctl.d/99-oracle-database-preinstall-19c-sysctl.conf
fs.file-max = 6815744
kernel.sem = 250 32000 100 128
kernel.shmmni = 4096
kernel.shmall = 1073741824
kernel.shmmax = 4398046511104
net.core.rmem_default = 262144
net.core.rmem_max = 4194304
net.core.wmem_default = 262144
net.core.wmem_max = 1048576
```

### 7.3 Senha do Usuário Oracle

```bash
# Define a senha do usuário oracle (criado pelo pacote preinstall)
echo 'oracle:Oracle19c#' | chpasswd

# Verifica grupos do usuário
id oracle
# Saída esperada: uid=54321(oracle) gid=54321(oinstall) groups=54321(oinstall),54322(dba),...
```

### 7.4 SELinux e Firewalld

```bash
# Desativa SELinux em tempo de execução (sem reboot)
setenforce 0

# Desativa SELinux permanentemente (persiste após reboot)
sed -i 's/^SELINUX=.*/SELINUX=disabled/' /etc/selinux/config

# Verifica estado atual
getenforce
# Saída esperada: Permissive

# Para e desabilita o firewall
# ATENÇÃO: em produção, configure as regras adequadas em vez de desabilitar
systemctl stop firewalld
systemctl disable firewalld
```

**Por quê:** O SELinux em modo Enforcing pode bloquear operações do Oracle (escrita em /u01, /u02, sockets de listener). Em laboratório, desabilitar é aceitável. Em produção, use políticas SELinux específicas para Oracle (`oracle-selinux` policy).

### 7.5 Estrutura de Diretórios

```bash
# ORACLE_HOME: onde os binários do Oracle serão instalados
mkdir -p /u01/app/oracle/product/19.03/dbhome_1

# ORACLE_INVENTORY: inventário de instalações Oracle no servidor
mkdir -p /u01/app/oraInventory

# Diretório de dados do banco (datafiles, redo logs, control files)
mkdir -p /u02/oradata

# Ajusta ownership e permissões
# oracle:oinstall garante que o usuário oracle possa escrever
chown -R oracle:oinstall /u01/app/oracle
chown -R oracle:oinstall /u01/app/oraInventory
chown -R oracle:oinstall /u02/oradata
chmod -R 775 /u01/app/oracle
chmod -R 775 /u01/app/oraInventory
chmod -R 775 /u02/oradata
```

**Por quê:** A Oracle exige essa separação de diretórios. `/u01` segue o padrão OFA (Optimal Flexible Architecture) da Oracle. `/u02` separa os datafiles do SO para facilitar backup e restauração.

### 7.6 Transferência do Instalador

```bash
# O ZIP é transferido via SCP/SFTP (~3 GB)
# Origem (Windows): D:\Install\oinstall\V982063-01-DB-193000-x86-64.zip
# Destino (VM): /tmp/V982063-01-DB-193000-x86-64.zip

# Ajusta ownership do ZIP
chown oracle:oinstall /tmp/V982063-01-DB-193000-x86-64.zip

# Descompacta diretamente no ORACLE_HOME como usuário oracle
su - oracle -c 'unzip -q /tmp/V982063-01-DB-193000-x86-64.zip -d /u01/app/oracle/product/19.03/dbhome_1'
```

---

## 8. Instalação Silenciosa do Oracle

### 8.1 Response File Completo

```ini
# /tmp/db_install.rsp — Instalação apenas do software (sem criar banco)
oracle.install.responseFileVersion=/oracle/install/rspfmt_dbinstall_response_schema_v19.0.0

# Instala apenas o software; o banco é criado separadamente via DBCA
oracle.install.option=INSTALL_DB_SWONLY

# Grupo principal do usuário oracle
UNIX_GROUP_NAME=oinstall

# Localização do inventário Oracle
INVENTORY_LOCATION=/u01/app/oraInventory

# Diretórios principais
ORACLE_HOME=/u01/app/oracle/product/19.03/dbhome_1
ORACLE_BASE=/u01/app/oracle

# Enterprise Edition
oracle.install.db.InstallEdition=EE

# Grupos de SO para cada papel de DBA
oracle.install.db.OSDBA_GROUP=dba
oracle.install.db.OSOPER_GROUP=oper
oracle.install.db.OSBACKUPDBA_GROUP=backupdba
oracle.install.db.OSDGDBA_GROUP=dgdba
oracle.install.db.OSKMDBA_GROUP=kmdba
oracle.install.db.OSRACDBA_GROUP=racdba

# Configuração dos scripts root (executados manualmente após instalação)
oracle.install.db.rootconfig.configMethod=ROOT
oracle.install.db.rootconfig.sudoUserName=
oracle.install.db.rootconfig.sudoRootEnabled=false
```

### 8.2 Comando de Instalação

```bash
export ORACLE_HOME=/u01/app/oracle/product/19.03/dbhome_1
export ORACLE_BASE=/u01/app/oracle
export CV_ASSUME_DISTID=OL8   # informa ao installer que é Oracle Linux 8

su - oracle -c '
$ORACLE_HOME/runInstaller \
  -silent \
  -ignorePrereq \
  -waitforcompletion \
  -responseFile /tmp/db_install.rsp
'
```

**Parâmetros explicados:**

| Parâmetro | Significado |
|-----------|-------------|
| `-silent` | Modo não-interativo, sem GUI |
| `-ignorePrereq` | Ignora avisos de pré-requisito (útil em lab) |
| `-waitforcompletion` | Aguarda conclusão e retorna no terminal |
| `-responseFile` | Arquivo com todas as respostas pré-definidas |
| `CV_ASSUME_DISTID=OL8` | Evita erro de "distro não suportada" no OL8 |

> **Nota:** O `runInstaller` pode retornar código 6 (warnings) mesmo em sucesso. Isso é normal quando há avisos de pré-requisito ignorados.

---

## 9. Scripts Root (Pós-instalação)

```bash
# 1. Configura o inventário Oracle no /etc/oraInst.loc
#    Cria o diretório do inventário e define o grupo oinstall
bash /u01/app/oraInventory/orainstRoot.sh

# Saída esperada:
# Changing permissions of /u01/app/oraInventory.
# Adding read,write permissions for group.
# Removing read,write,execute permissions for world.
# Changing groupname of /u01/app/oraInventory to oinstall.
# The execution of the script is complete.

# 2. Configura links de bibliotecas, variáveis de kernel e Oracle DBMS
#    DEVE ser executado como root
bash /u01/app/oracle/product/19.03/dbhome_1/root.sh

# Saída esperada:
# Performing root user operation.
# The following environment variables are set as:
#   ORACLE_OWNER= oracle
#   ORACLE_HOME=  /u01/app/oracle/product/19.03/dbhome_1
# Enter the full pathname of the local bin directory: [/usr/local/bin]:
# /usr/local/bin is read by root, continuing with Oracle installation for this Ant Project.
# Creating /etc/oratab file...
# Entries will be added to the /etc/oratab file as needed by
#   Database Configuration Assistant when a database is created
# Finished running generic part of root script.
```

---

## 10. Criação do Banco via DBCA

```bash
su - oracle -c '
dbca -silent -createDatabase \
  -templateName General_Purpose.dbc \
  -gdbname orcl.localdomain \
  -sid orcl \
  -createAsContainerDatabase true \
  -numberOfPDBs 1 \
  -pdbName orclpdb \
  -pdbAdminPassword "Oracle19c#" \
  -databaseType MULTIPURPOSE \
  -characterSet AL32UTF8 \
  -nationalCharacterSet AL16UTF16 \
  -sysPassword "Oracle19c#" \
  -systemPassword "Oracle19c#" \
  -datafileDestination "/u02/oradata" \
  -recoveryAreaDestination "/u02/oradata/fast_recovery_area" \
  -recoveryAreaSize 10240 \
  -enableArchive false \
  -memoryMgmtType auto_sga \
  -totalMemory 1536 \
  -emConfiguration DBEXPRESS \
  -emExpressPort 5500 \
  -ignorePrereqs
'
```

**Parâmetros do DBCA explicados:**

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| `-templateName` | `General_Purpose.dbc` | Template balanceado para OLTP |
| `-gdbname` | `orcl.localdomain` | Nome global do banco (db_name.db_domain) |
| `-sid` | `orcl` | Identificador da instância Oracle |
| `-createAsContainerDatabase` | `true` | Arquitetura CDB (obrigatório 19c para PDB) |
| `-numberOfPDBs` | `1` | Cria 1 Pluggable Database |
| `-pdbName` | `orclpdb` | Nome do PDB |
| `-characterSet` | `AL32UTF8` | Charset Unicode (recomendado Oracle) |
| `-nationalCharacterSet` | `AL16UTF16` | N-Char para tipos NCHAR/NVARCHAR2 |
| `-datafileDestination` | `/u02/oradata` | Localização dos datafiles |
| `-recoveryAreaSize` | `10240` | FRA: 10 GB |
| `-enableArchive` | `false` | Sem archivelog (lab) — em prod: `true` |
| `-memoryMgmtType` | `auto_sga` | AMM automático |
| `-totalMemory` | `1536` | 1,5 GB total para Oracle |
| `-emConfiguration` | `DBEXPRESS` | Habilita EM Express (porta 5500) |

---

## 11. Estrutura de Diretórios Criada

```
/
├── u01/                          # Binários Oracle (OFA padrão)
│   └── app/
│       ├── oraInventory/         # Inventário de instalações Oracle
│       │   └── ContentsXML/      # Registro dos ORACLE_HOMEs
│       └── oracle/               # ORACLE_BASE
│           ├── admin/            # Configurações de instância (alert log, trace)
│           │   └── orcl/
│           │       ├── adump/    # Audit trail
│           │       ├── bdump/    # Background dumps (alert log)
│           │       ├── cdump/    # Core dumps
│           │       └── udump/    # User dumps
│           ├── diag/             # Diagnostic destination (ADR)
│           └── product/
│               └── 19.03/
│                   └── dbhome_1/ # ORACLE_HOME (binários, libs, OPatch)
│                       ├── bin/  # sqlplus, rman, dgmgrl, impdp, expdp...
│                       ├── lib/  # Bibliotecas compartilhadas
│                       ├── rdbms/
│                       └── ...
└── u02/                          # Dados Oracle (separado do SO)
    └── oradata/
        ├── ORCL/                 # Datafiles do CDB
        │   ├── system01.dbf      # Tablespace SYSTEM
        │   ├── sysaux01.dbf      # Tablespace SYSAUX
        │   ├── undotbs01.dbf     # Tablespace UNDO
        │   ├── users01.dbf       # Tablespace USERS
        │   └── redo0{1,2,3}.log  # Online redo logs
        ├── ORCLPDB/              # Datafiles do PDB orclpdb
        └── fast_recovery_area/   # FRA para backups e archived logs
```

---

## 12. Variáveis de Ambiente Oracle

Configuradas em `/home/oracle/.bash_profile`:

```bash
# Oracle Environment
export ORACLE_BASE=/u01/app/oracle
export ORACLE_HOME=/u01/app/oracle/product/19.03/dbhome_1
export ORACLE_SID=orcl

# Configurações de localização/formato
export NLS_DATE_FORMAT='DD/MM/YYYY HH24:MI:SS'
export NLS_LANG=AMERICAN_AMERICA.AL32UTF8

# PATH: inclui binários Oracle e OPatch (para patches)
export PATH=$ORACLE_HOME/bin:$ORACLE_HOME/OPatch:$PATH

# Bibliotecas compartilhadas
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:/lib:/usr/lib

# Java classpath Oracle
export CLASSPATH=$ORACLE_HOME/jlib:$ORACLE_HOME/rdbms/jlib

# Aliases úteis
alias sqlp='sqlplus / as sysdba'
alias startup='sqlplus / as sysdba <<< "startup"'
alias shutdown_i='sqlplus / as sysdba <<< "shutdown immediate"'
```

**Por que cada variável:**

| Variável | Motivo |
|----------|--------|
| `ORACLE_BASE` | Raiz para todos os arquivos de diagnóstico e admin |
| `ORACLE_HOME` | Localiza binários (sqlplus, rman), libs e configurações |
| `ORACLE_SID` | Identifica qual instância o sqlplus e rman conectam |
| `NLS_DATE_FORMAT` | Evita ambiguidade de datas no SQL |
| `NLS_LANG` | Define encoding do cliente; deve bater com o banco |
| `LD_LIBRARY_PATH` | Necessário para Oracle libs em algumas distros |

---

## 13. Serviço Systemd

Arquivo: `/etc/systemd/system/oracle-database.service`

```ini
[Unit]
Description=Oracle Database 19c (orcl)
After=network.target

[Service]
Type=forking
User=oracle
Group=oinstall
Environment="ORACLE_HOME=/u01/app/oracle/product/19.03/dbhome_1"
Environment="ORACLE_BASE=/u01/app/oracle"
Environment="ORACLE_SID=orcl"
Environment="PATH=/u01/app/oracle/product/19.03/dbhome_1/bin:/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin"
ExecStart=/u01/app/oracle/product/19.03/dbhome_1/bin/dbstart /u01/app/oracle/product/19.03/dbhome_1
ExecStop=/u01/app/oracle/product/19.03/dbhome_1/bin/dbshut /u01/app/oracle/product/19.03/dbhome_1
TimeoutStartSec=900
TimeoutStopSec=300

[Install]
WantedBy=multi-user.target
```

**Comandos de gerenciamento:**

```bash
# Habilitar (já feito pelo script)
systemctl enable oracle-database

# Iniciar o banco
systemctl start oracle-database

# Parar o banco
systemctl stop oracle-database

# Verificar status
systemctl status oracle-database

# Ver logs do serviço
journalctl -u oracle-database -f
```

**Dependência: `/etc/oratab`**

O `dbstart` e `dbshut` só iniciam/param instâncias marcadas com `Y` no oratab:

```
# /etc/oratab — formato: SID:ORACLE_HOME:AUTO_START
orcl:/u01/app/oracle/product/19.03/dbhome_1:Y
```

---

## 14. Comandos de Validação e Saída Esperada

### 14.1 Verificar Status da Instância

```sql
-- Conectar como SYSDBA
sqlplus / as sysdba

-- Verificar instância
SELECT instance_name, host_name, version, status, database_status
FROM v$instance;

-- Saída esperada:
-- INSTANCE_NAME  HOST_NAME              VERSION           STATUS     DATABASE_STATUS
-- -------------- ---------------------- ----------------- ---------- -----------------
-- orcl           ol8-dba.localdomain    19.0.0.0.0        OPEN       ACTIVE
```

### 14.2 Verificar CDB e PDB

```sql
-- Banco CDB
SELECT name, db_unique_name, cdb, con_id FROM v$database;

-- Saída esperada:
-- NAME     DB_UNIQUE_NAME CDB     CON_ID
-- -------- -------------- ------- ------
-- ORCL     orcl           YES          0

-- Listar PDBs
SELECT con_id, name, open_mode FROM v$pdbs;

-- Saída esperada:
-- CON_ID NAME        OPEN_MODE
-- ------ ----------- ----------
--      2 PDB$SEED    READ ONLY
--      3 ORCLPDB     READ WRITE
```

### 14.3 Verificar Processos Background

```bash
ps -ef | grep pmon
# Saída esperada:
# oracle  1234  ... ora_pmon_orcl
```

### 14.4 Verificar Listener

```bash
su - oracle -c 'lsnrctl status'

# Saída esperada:
# LSNRCTL for Linux: Version 19.0.0.0.0
# ...
# STATUS of the LISTENER
# Alias                     LISTENER
# Version                   TNSLSNR for Linux: Version 19.0.0.0.0
# Start Date                16-MAY-2026 10:00:00
# Uptime                    0 days 0 hr. 5 min. 0 sec
# ...
# Services Summary...
# Service "orcl.localdomain" has 1 instance(s).
# Service "orclpdb.localdomain" has 1 instance(s).
# The command completed successfully
```

### 14.5 Acessar EM Express

```
URL    : https://192.168.56.101:5500/em
Usuário: SYS
Senha  : Oracle19c#
Role   : SYSDBA

# Para acesso ao PDB via EM Express:
URL    : https://192.168.56.101:5500/em?pdbName=orclpdb
```

---

## 15. Troubleshooting — Erros Comuns

### 15.1 INS-30131: Falha na execução do pré-requisito

**Erro:** `INS-30131: Initial setup required for the execution of installer validations failed`

**Causa:** Geralmente ocorre quando o `/tmp` não tem permissão de execução ou o usuário oracle não tem acesso.

**Solução:**
```bash
chmod 1777 /tmp
su - oracle -c 'ls /tmp'   # Verifica acesso
```

### 15.2 OUI-10133: ORACLE_HOME já existe

**Erro:** `OUI-10133: There are no empty directories available for Oracle Home creation`

**Causa:** O diretório `ORACLE_HOME` já contém arquivos de uma instalação anterior incompleta.

**Solução:**
```bash
rm -rf /u01/app/oracle/product/19.03/dbhome_1/*
mkdir -p /u01/app/oracle/product/19.03/dbhome_1
chown oracle:oinstall /u01/app/oracle/product/19.03/dbhome_1
```

### 15.3 DBCA: ORA-12547 ou TNS:lost contact

**Causa:** O listener não está ativo durante a criação do banco.

**Solução:**
```bash
su - oracle -c 'lsnrctl start'
# Em seguida, reexecutar o DBCA
```

### 15.4 Parâmetros de Kernel insuficientes

**Erro:** `PRVF-7531 / PRVF-7532: Semaphore parameters check failed`

**Causa:** O pacote `oracle-database-preinstall-19c` não foi instalado ou não foi aplicado.

**Solução:**
```bash
# Verificar se foi instalado
rpm -q oracle-database-preinstall-19c

# Aplicar manualmente os parâmetros de kernel
sysctl -p /etc/sysctl.d/99-oracle-database-preinstall-19c-sysctl.conf
```

### 15.5 ORA-01034: ORACLE not available

**Causa:** A instância não está aberta — pode ser problema de ORACLE_SID errado ou banco parado.

**Solução:**
```bash
export ORACLE_SID=orcl
sqlplus / as sysdba
SQL> startup;

# Verificar alert log
tail -100 /u01/app/oracle/diag/rdbms/orcl/orcl/trace/alert_orcl.log
```

### 15.6 Espaço insuficiente em /tmp durante instalação

**Erro:** `Unpacking installer: failed with insufficient space`

**Solução:**
```bash
df -h /tmp
# Se < 3 GB livres:
mount -t tmpfs -o size=4G tmpfs /tmp
```

### 15.7 CV_ASSUME_DISTID necessário no OL8

**Causa:** O installer 19.3.0 pode não reconhecer OL 8.x sem essa variável.

**Solução:**
```bash
export CV_ASSUME_DISTID=OL8
# Sempre exportar antes de executar runInstaller
```

### 15.8 Banco não inicia automaticamente após reboot

**Causa:** `/etc/oratab` com flag `N` ou serviço systemd não habilitado.

**Solução:**
```bash
# Verificar oratab
grep orcl /etc/oratab
# Deve mostrar: orcl:/u01/app/oracle/product/19.03/dbhome_1:Y
# Corrigir se necessário:
sed -i 's/orcl:.*:N/orcl:\/u01\/app\/oracle\/product\/19.03\/dbhome_1:Y/' /etc/oratab

# Verificar serviço
systemctl is-enabled oracle-database
systemctl enable oracle-database
```

---

## 16. Resumo Final da Instalação

| Item | Valor |
|------|-------|
| **Versão Oracle** | 19.3.0.0.0 Enterprise Edition |
| **ORACLE_BASE** | `/u01/app/oracle` |
| **ORACLE_HOME** | `/u01/app/oracle/product/19.03/dbhome_1` |
| **ORACLE_SID** | `orcl` |
| **Global DB Name** | `orcl.localdomain` |
| **PDB** | `orclpdb` |
| **Character Set** | `AL32UTF8` |
| **Datafiles** | `/u02/oradata` |
| **EM Express** | `https://192.168.56.101:5500/em` |
| **Porta Listener** | `1521` |
| **Senha SYS/SYSTEM** | `Oracle19c#` |

---

## 17. Referências e Links Úteis

| Recurso | URL |
|---------|-----|
| Oracle DB 19c Documentation Hub | https://docs.oracle.com/en/database/oracle/oracle-database/19/ |
| Oracle DB 19c Backup and Recovery Guide (BRADV) | https://docs.oracle.com/en/database/oracle/oracle-database/19/bradv/ |
| Oracle DB 19c RMAN Reference (RCMRF) | https://docs.oracle.com/en/database/oracle/oracle-database/19/rcmrf/ |
| Oracle Linux 8 Documentation | https://docs.oracle.com/en/operating-systems/oracle-linux/8/ |
| Oracle Database Installation Guide 19c Linux | https://docs.oracle.com/en/database/oracle/oracle-database/19/ladbi/ |
| My Oracle Support | https://support.oracle.com |
| OFA (Optimal Flexible Architecture) | https://docs.oracle.com/en/database/oracle/oracle-database/19/ladbi/optimal-flexible-architecture-file-path-examples.html |
| Oracle Preinstall Package | https://yum.oracle.com/repo/OracleLinux/OL8/appstream/x86_64/index.html |
| Paramiko (SSH Python) | https://www.paramiko.org/ |

---

*Documento gerado automaticamente durante a Imersão Oracle Backup & Recovery.*  
*Para dúvidas, consulte a documentação oficial Oracle listada nas referências acima.*
