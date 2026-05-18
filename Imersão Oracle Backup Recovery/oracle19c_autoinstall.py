#!/usr/bin/env python3
"""
=============================================================================
oracle19c_autoinstall.py
Automação completa da instalação do Oracle Database 19c Enterprise Edition
em Oracle Linux 8.x via SSH/SCP usando Paramiko.

Autor  : DBA Oracle - Imersão Backup & Recovery
Data   : 2026-05-16
Versão : 1.0

COMO USAR:
  1. pip install paramiko
  2. python oracle19c_autoinstall.py
=============================================================================
"""

import sys
import os
import time
import socket
import paramiko
from pathlib import Path

# ─────────────────────────── CONFIGURAÇÕES ───────────────────────────────────
VM_HOST         = "192.168.56.101"
VM_PORT         = 22
VM_USER         = "root"
VM_PASSWORD     = "Welcome#"
SSH_KEY_PATH    = r"C:\Users\Flavio.Melo\.ssh\id_ed25519"   # tenta chave primeiro

# Instalador Oracle no Windows
LOCAL_ZIP       = r"D:\Install\oinstall\V982063-01-DB-193000-x86-64.zip"
REMOTE_ZIP_DIR  = "/tmp"          # destino temporário na VM
REMOTE_ZIP      = "/tmp/V982063-01-DB-193000-x86-64.zip"

# Parâmetros Oracle
ORACLE_BASE     = "/u01/app/oracle"
ORACLE_HOME     = "/u01/app/oracle/product/19.03/dbhome_1"
ORACLE_INV      = "/u01/app/oraInventory"
DATA_DIR        = "/u02/oradata"
DB_NAME         = "orcl"
DB_DOMAIN       = "localdomain"
PDB_NAME        = "orclpdb"
SYS_PASSWORD    = "Oracle19c#"
CHARSET         = "AL32UTF8"
HOSTNAME        = "ol8-dba.localdomain"
# ─────────────────────────────────────────────────────────────────────────────


YELLOW = "\033[93m"
GREEN  = "\033[92m"
RED    = "\033[91m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def log(msg, color=RESET):    print(f"{color}{msg}{RESET}", flush=True)
def ok(msg):                  log(f"  ✔  {msg}", GREEN)
def warn(msg):                log(f"  ⚠  {msg}", YELLOW)
def err(msg):                 log(f"  ✘  {msg}", RED)
def step(n, total, msg):      log(f"\n{BOLD}{CYAN}[{n}/{total}] {msg}{RESET}")
def banner(msg):
    line = "═" * 70
    log(f"\n{BOLD}{CYAN}{line}\n  {msg}\n{line}{RESET}")


def conectar_ssh() -> paramiko.SSHClient:
    """Abre conexão SSH com chave ou senha."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Tenta com chave Ed25519
    key_path = Path(SSH_KEY_PATH)
    if key_path.exists():
        try:
            key = paramiko.Ed25519Key.from_private_key_file(str(key_path))
            client.connect(VM_HOST, port=VM_PORT, username=VM_USER, pkey=key,
                           timeout=30, banner_timeout=30)
            ok(f"Conectado via chave SSH: {SSH_KEY_PATH}")
            return client
        except Exception as e:
            warn(f"Chave SSH falhou ({e}), tentando senha...")

    # Fallback: senha
    client.connect(VM_HOST, port=VM_PORT, username=VM_USER,
                   password=VM_PASSWORD, timeout=30, banner_timeout=30,
                   look_for_keys=False, allow_agent=False)
    ok("Conectado via senha SSH")
    return client


def run(client: paramiko.SSHClient, cmd: str, timeout=120, check=True) -> tuple[int, str, str]:
    """Executa comando remoto e retorna (exit_code, stdout, stderr)."""
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout, get_pty=False)
    out = stdout.read().decode(errors="replace").strip()
    err_out = stderr.read().decode(errors="replace").strip()
    rc = stdout.channel.recv_exit_status()
    if check and rc != 0:
        err(f"COMANDO FALHOU (rc={rc}): {cmd}")
        if err_out:
            err(f"STDERR: {err_out}")
        raise SystemExit(1)
    return rc, out, err_out


def run_show(client: paramiko.SSHClient, cmd: str, timeout=120, check=True) -> tuple[int, str, str]:
    """Executa e imprime saída em tempo real (linha a linha via canal)."""
    transport = client.get_transport()
    chan = transport.open_session()
    chan.get_pty()
    chan.exec_command(cmd)
    buf = ""
    full = ""
    while True:
        data = chan.recv(4096)
        if not data:
            break
        chunk = data.decode(errors="replace")
        full += chunk
        for line in (buf + chunk).splitlines(True):
            if line.endswith("\n") or line.endswith("\r"):
                print(f"    {line.rstrip()}", flush=True)
                buf = ""
            else:
                buf = line
    if buf:
        print(f"    {buf}", flush=True)
    rc = chan.recv_exit_status()
    if check and rc != 0:
        err(f"COMANDO FALHOU (rc={rc}): {cmd}")
        raise SystemExit(1)
    return rc, full, ""


def scp_upload(client: paramiko.SSHClient, local_path: str, remote_path: str):
    """Envia arquivo local → VM via SFTP com barra de progresso."""
    local = Path(local_path)
    if not local.exists():
        err(f"Arquivo local não encontrado: {local_path}")
        raise SystemExit(1)

    size_gb = local.stat().st_size / 1024**3
    log(f"  → Transferindo {local.name} ({size_gb:.2f} GB) para {remote_path} ...")
    log("    (isso pode levar vários minutos dependendo da interface de rede)")

    sftp = client.open_sftp()
    transferred = [0]
    start = time.time()

    def progress(sent, total):
        pct = sent * 100 // total
        elapsed = time.time() - start
        speed = sent / elapsed / 1024**2 if elapsed > 0 else 0
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
        print(f"\r    [{bar}] {pct:3d}%  {speed:5.1f} MB/s", end="", flush=True)

    sftp.put(local_path, remote_path, callback=progress)
    sftp.close()
    elapsed = time.time() - start
    print(f"\r    [████████████████████] 100%  ({elapsed:.0f}s)            ")
    ok(f"Arquivo transferido com sucesso em {elapsed:.0f}s")


# ══════════════════════════════════════════════════════════════════════════════
# ETAPAS DA INSTALAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

def etapa_configurar_hosts(client):
    step(1, 10, "Configurar /etc/hosts e hostname")
    # Remove entradas antigas e adiciona nova
    run(client, f"""
IP=$(hostname -I | awk '{{print $1}}')
# remove linha com ol8-dba se existir
sed -i '/ol8-dba/d' /etc/hosts
# adiciona entrada
echo "192.168.56.101  {HOSTNAME}  ol8-dba" >> /etc/hosts
hostnamectl set-hostname {HOSTNAME}
hostname
""")
    _, out, _ = run(client, "hostname")
    ok(f"Hostname configurado: {out}")


def etapa_instalar_preinstall(client):
    step(2, 10, "Instalar oracle-database-preinstall-19c via YUM")
    log("  (pode demorar 2-5 min)")
    run_show(client, """
dnf install -y oracle-database-preinstall-19c 2>&1
""", timeout=600)
    ok("Pacote oracle-database-preinstall-19c instalado")


def etapa_configurar_oracle_user(client):
    step(3, 10, "Definir senha do usuário oracle e grupos")
    run(client, f"echo 'oracle:{SYS_PASSWORD}' | chpasswd")
    run(client, "id oracle")
    _, out, _ = run(client, "id oracle")
    ok(f"Usuário oracle: {out}")


def etapa_desabilitar_selinux_firewall(client):
    step(4, 10, "Desabilitar SELinux e Firewalld")
    # SELinux
    run(client, "setenforce 0 || true")
    run(client, "sed -i 's/^SELINUX=.*/SELINUX=disabled/' /etc/selinux/config")
    _, out, _ = run(client, "getenforce")
    ok(f"SELinux: {out}")
    # Firewalld
    run(client, "systemctl stop firewalld 2>/dev/null || true")
    run(client, "systemctl disable firewalld 2>/dev/null || true")
    ok("Firewalld desabilitado")


def etapa_criar_diretorios(client):
    step(5, 10, "Criar estrutura de diretórios Oracle")
    cmds = [
        f"mkdir -p {ORACLE_HOME}",
        f"mkdir -p {ORACLE_INV}",
        f"mkdir -p {DATA_DIR}",
        f"chown -R oracle:oinstall {ORACLE_BASE}",
        f"chown -R oracle:oinstall {ORACLE_INV}",
        f"chown -R oracle:oinstall {DATA_DIR}",
        f"chmod -R 775 {ORACLE_BASE}",
        f"chmod -R 775 {ORACLE_INV}",
        f"chmod -R 775 {DATA_DIR}",
    ]
    for cmd in cmds:
        run(client, cmd)
    ok(f"Diretórios criados:")
    ok(f"  ORACLE_HOME : {ORACLE_HOME}")
    ok(f"  ORACLE_INV  : {ORACLE_INV}")
    ok(f"  DATA_DIR    : {DATA_DIR}")


def etapa_transferir_instalador(client):
    step(6, 10, "Transferir e descompactar instalador Oracle")
    # Verifica se já foi transferido
    rc, _, _ = run(client, f"test -f {REMOTE_ZIP}", check=False)
    if rc == 0:
        warn(f"ZIP já existe em {REMOTE_ZIP} — pulando transferência")
    else:
        scp_upload(client, LOCAL_ZIP, REMOTE_ZIP)

    # Descompacta no ORACLE_HOME como oracle
    log(f"  → Descompactando ZIP em {ORACLE_HOME} (pode demorar 3-8 min)...")
    run(client, f"chown oracle:oinstall {REMOTE_ZIP}")
    run_show(client,
        f"su - oracle -c 'unzip -q {REMOTE_ZIP} -d {ORACLE_HOME}'",
        timeout=900)
    # Verifica runInstaller
    rc, _, _ = run(client, f"test -f {ORACLE_HOME}/runInstaller", check=False)
    if rc != 0:
        err(f"runInstaller não encontrado em {ORACLE_HOME} — verifique o ZIP")
        raise SystemExit(1)
    ok(f"Instalador descompactado em {ORACLE_HOME}")


def etapa_criar_response_file(client):
    """Cria o response file para instalação silenciosa."""
    response = f"""oracle.install.responseFileVersion=/oracle/install/rspfmt_dbinstall_response_schema_v19.0.0
oracle.install.option=INSTALL_DB_SWONLY
UNIX_GROUP_NAME=oinstall
INVENTORY_LOCATION={ORACLE_INV}
ORACLE_HOME={ORACLE_HOME}
ORACLE_BASE={ORACLE_BASE}
oracle.install.db.InstallEdition=EE
oracle.install.db.OSDBA_GROUP=dba
oracle.install.db.OSOPER_GROUP=oper
oracle.install.db.OSBACKUPDBA_GROUP=backupdba
oracle.install.db.OSDGDBA_GROUP=dgdba
oracle.install.db.OSKMDBA_GROUP=kmdba
oracle.install.db.OSRACDBA_GROUP=racdba
oracle.install.db.rootconfig.configMethod=ROOT
oracle.install.db.rootconfig.sudoUserName=
oracle.install.db.rootconfig.sudoRootEnabled=false
"""
    run(client, f"cat > /tmp/db_install.rsp << 'RSPEOF'\n{response}\nRSPEOF")
    run(client, f"chown oracle:oinstall /tmp/db_install.rsp")
    ok("Response file criado: /tmp/db_install.rsp")


def etapa_instalar_oracle_software(client):
    step(7, 10, "Executar instalação silenciosa do Oracle Software")
    log("  (esse processo leva 15-40 minutos — aguarde)")

    # Cria response file
    etapa_criar_response_file(client)

    # Seta variáveis e executa installer
    install_cmd = f"""export ORACLE_HOME={ORACLE_HOME}
export ORACLE_BASE={ORACLE_BASE}
export CV_ASSUME_DISTID=OL8
{ORACLE_HOME}/runInstaller -silent -ignorePrereq -waitforcompletion \\
  -responseFile /tmp/db_install.rsp \\
  ORACLE_HOME={ORACLE_HOME} \\
  ORACLE_BASE={ORACLE_BASE} \\
  2>&1
"""
    run_show(client,
        f"su - oracle -c '{install_cmd}'",
        timeout=3600, check=False)  # não check aqui; runInstaller retorna 6 (warnings)

    # Verifica log de instalação
    _, out, _ = run(client,
        f"ls -t /tmp/InstallActions*/installActions*.log 2>/dev/null | head -1",
        check=False)
    if out:
        _, log_tail, _ = run(client, f"tail -20 '{out}'", check=False)
        log(f"  Últimas linhas do log de instalação:\n{log_tail}")

    ok("Instalação do software Oracle concluída")


def etapa_executar_root_scripts(client):
    step(8, 10, "Executar orainstRoot.sh e root.sh")
    # orainstRoot.sh
    log("  → Executando orainstRoot.sh ...")
    run_show(client, f"bash {ORACLE_INV}/orainstRoot.sh 2>&1", timeout=120)
    ok("orainstRoot.sh executado")

    # root.sh
    log("  → Executando root.sh ...")
    run_show(client, f"bash {ORACLE_HOME}/root.sh 2>&1", timeout=300)
    ok("root.sh executado")


def etapa_criar_banco(client):
    """Cria o banco de dados usando DBCA em modo silencioso."""
    step(9, 10, "Criar banco de dados orcl (DBCA silencioso)")
    log("  (criação do banco leva 20-45 minutos — aguarde)")

    dbca_cmd = f"""export ORACLE_HOME={ORACLE_HOME}
export ORACLE_BASE={ORACLE_BASE}
export ORACLE_SID={DB_NAME}
export PATH=$ORACLE_HOME/bin:$PATH
dbca -silent -createDatabase \\
  -templateName General_Purpose.dbc \\
  -gdbname {DB_NAME}.{DB_DOMAIN} \\
  -sid {DB_NAME} \\
  -createAsContainerDatabase true \\
  -numberOfPDBs 1 \\
  -pdbName {PDB_NAME} \\
  -pdbAdminPassword "{SYS_PASSWORD}" \\
  -databaseType MULTIPURPOSE \\
  -characterSet {CHARSET} \\
  -nationalCharacterSet AL16UTF16 \\
  -sysPassword "{SYS_PASSWORD}" \\
  -systemPassword "{SYS_PASSWORD}" \\
  -datafileDestination "{DATA_DIR}" \\
  -recoveryAreaDestination "{DATA_DIR}/fast_recovery_area" \\
  -recoveryAreaSize 10240 \\
  -enableArchive false \\
  -memoryMgmtType auto_sga \\
  -totalMemory 1536 \\
  -emConfiguration DBEXPRESS \\
  -emExpressPort 5500 \\
  -J-Doracle.assistants.dbca.validate.DBCredentials=false \\
  -ignorePrereqs \\
  2>&1
"""
    run_show(client,
        f"su - oracle -c \"{dbca_cmd}\"",
        timeout=5400, check=False)
    ok("Banco de dados orcl criado")


def etapa_configurar_ambiente(client):
    """Configura .bash_profile, oratab e serviço systemd."""

    # .bash_profile do oracle
    bash_profile = f"""
# Oracle Environment
export ORACLE_BASE={ORACLE_BASE}
export ORACLE_HOME={ORACLE_HOME}
export ORACLE_SID={DB_NAME}
export NLS_DATE_FORMAT='DD/MM/YYYY HH24:MI:SS'
export NLS_LANG=AMERICAN_AMERICA.AL32UTF8
export PATH=$ORACLE_HOME/bin:$ORACLE_HOME/OPatch:$PATH
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:/lib:/usr/lib
export CLASSPATH=$ORACLE_HOME/jlib:$ORACLE_HOME/rdbms/jlib
alias sqlp='sqlplus / as sysdba'
alias startup='sqlplus / as sysdba <<< "startup"'
alias shutdown_i='sqlplus / as sysdba <<< "shutdown immediate"'
"""
    run(client, f"""cat >> /home/oracle/.bash_profile << 'BPEOF'
{bash_profile}
BPEOF
""")
    ok(".bash_profile do oracle configurado")

    # /etc/oratab
    run(client,
        f"sed -i 's|{DB_NAME}:.*|{DB_NAME}:{ORACLE_HOME}:Y|' /etc/oratab || "
        f"echo '{DB_NAME}:{ORACLE_HOME}:Y' >> /etc/oratab")
    ok("/etc/oratab configurado")

    # Serviço systemd
    service_content = f"""[Unit]
Description=Oracle Database 19c ({DB_NAME})
After=network.target

[Service]
Type=forking
User=oracle
Group=oinstall
Environment="ORACLE_HOME={ORACLE_HOME}"
Environment="ORACLE_BASE={ORACLE_BASE}"
Environment="ORACLE_SID={DB_NAME}"
Environment="PATH={ORACLE_HOME}/bin:/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin"
ExecStart={ORACLE_HOME}/bin/dbstart {ORACLE_HOME}
ExecStop={ORACLE_HOME}/bin/dbshut {ORACLE_HOME}
TimeoutStartSec=900
TimeoutStopSec=300

[Install]
WantedBy=multi-user.target
"""
    run(client, f"""cat > /etc/systemd/system/oracle-database.service << 'SVCEOF'
{service_content}
SVCEOF
""")
    run(client, "systemctl daemon-reload")
    run(client, "systemctl enable oracle-database.service")
    ok("Serviço systemd oracle-database criado e habilitado")


def etapa_validar(client):
    step(10, 10, "Validar instalação via SQLPlus")

    validation_sql = f"""
export ORACLE_HOME={ORACLE_HOME}
export ORACLE_BASE={ORACLE_BASE}
export ORACLE_SID={DB_NAME}
export PATH=$ORACLE_HOME/bin:$PATH
sqlplus -s / as sysdba << 'SQLEOF'
SET LINESIZE 120
SET PAGESIZE 50
COLUMN INSTANCE_NAME FORMAT A12
COLUMN HOST_NAME FORMAT A20
COLUMN VERSION FORMAT A15
COLUMN STATUS FORMAT A10
COLUMN DATABASE_STATUS FORMAT A17
SELECT
    INSTANCE_NAME,
    HOST_NAME,
    VERSION,
    STATUS,
    DATABASE_STATUS
FROM V$INSTANCE;
SELECT NAME, DB_UNIQUE_NAME, CDB, CON_ID FROM V$DATABASE;
SELECT CON_ID, NAME, OPEN_MODE FROM V$PDBS;
EXIT;
SQLEOF
"""
    _, out, _ = run(client,
        f"su - oracle -c \"{validation_sql}\"",
        timeout=60, check=False)
    log(f"\n{BOLD}  ─── Saída do SQLPlus ───{RESET}")
    for line in out.splitlines():
        print(f"    {line}")

    # EM Express URL
    _, em_port, _ = run(client,
        f"su - oracle -c 'export ORACLE_HOME={ORACLE_HOME}; export PATH=$ORACLE_HOME/bin:$PATH; "
        f"export ORACLE_SID={DB_NAME}; "
        f"sqlplus -s / as sysdba <<< \"select dbms_xdb_config.gethttpsport() from dual;\"'",
        check=False)
    port_num = em_port.strip().split()[-1] if em_port.strip() else "5500"

    banner("INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
    log(f"""
  {BOLD}Resumo da Instalação{RESET}
  ─────────────────────────────────────────
  ORACLE_BASE    : {ORACLE_BASE}
  ORACLE_HOME    : {ORACLE_HOME}
  ORACLE_SID     : {DB_NAME}
  Global DB Name : {DB_NAME}.{DB_DOMAIN}
  PDB            : {PDB_NAME}
  Character Set  : {CHARSET}
  Data Location  : {DATA_DIR}
  Versão         : Oracle Database 19c EE

  {BOLD}EM Express{RESET}
  URL            : https://192.168.56.101:{port_num}/em
  Usuário        : SYS (as SYSDBA)
  Senha          : {SYS_PASSWORD}

  {BOLD}Serviço Systemd{RESET}
  Iniciar        : systemctl start oracle-database
  Parar          : systemctl stop oracle-database
  Status         : systemctl status oracle-database
  ─────────────────────────────────────────
""", CYAN)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    banner("Oracle Database 19c - Instalação Automatizada")
    log(f"  Host alvo  : {VM_HOST}:{VM_PORT}")
    log(f"  ORACLE_HOME: {ORACLE_HOME}")
    log(f"  SID        : {DB_NAME}")
    log(f"  PDB        : {PDB_NAME}")

    # ── Conecta SSH ──────────────────────────────────────────────────────────
    log(f"\n  Conectando em {VM_USER}@{VM_HOST}...")
    try:
        client = conectar_ssh()
    except Exception as e:
        err(f"Falha na conexão SSH: {e}")
        sys.exit(1)

    try:
        etapa_configurar_hosts(client)
        etapa_instalar_preinstall(client)
        etapa_configurar_oracle_user(client)
        etapa_desabilitar_selinux_firewall(client)
        etapa_criar_diretorios(client)
        etapa_transferir_instalador(client)
        etapa_instalar_oracle_software(client)
        etapa_executar_root_scripts(client)
        etapa_criar_banco(client)
        etapa_configurar_ambiente(client)
        etapa_validar(client)
    except SystemExit:
        err("\nInstalação interrompida por erro. Verifique os logs acima.")
        sys.exit(1)
    except KeyboardInterrupt:
        warn("\nInstalação interrompida pelo usuário.")
        sys.exit(2)
    finally:
        client.close()


if __name__ == "__main__":
    main()
