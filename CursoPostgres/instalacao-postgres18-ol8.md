# Instalação PostgreSQL 18 — Oracle Linux 8.10

> VM de treinamento: `192.168.56.21` | Distro: Oracle Linux 8.10 | PG: 18.4
> Baseado no tutorial do curso (PG16/Ubuntu) — adaptado para OL8/PG18
> Executado em: 2026-06-28

---

## 1. Conectividade SSH

Copiar chave pública para root (executar no Windows, uma vez):

```powershell
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh root@192.168.56.21 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
```

Testar:

```powershell
ssh root@192.168.56.21
```

---

## 2. Atualizar o sistema

> Passo equivalente ao `apt update && apt upgrade` do tutorial original.
> **Não executado na instalação inicial** — recomendado antes de novo ambiente.

```bash
sudo dnf update -y
```

---

## 3. Repositório PGDG

```bash
sudo dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-8-x86_64/pgdg-redhat-repo-latest.noarch.rpm
sudo dnf -qy module disable postgresql   # desabilita módulo AppStream do OL8
```

> Na VM 192.168.56.21 o repo já estava instalado (pgdg-redhat-repo-42.0-65).

---

## 4. Instalar pacotes

```bash
sudo dnf install -y postgresql18-server postgresql18-contrib
```

> Versão instalada: `postgresql18-18.4-2PGDG.rhel8.10.x86_64`

---

## 5. Locale pt_BR

O pacote de locale português não estava presente na VM — necessário para o `initdb`.

```bash
sudo dnf install -y glibc-langpack-pt
```

> No Ubuntu o locale costuma vir pré-instalado. No OL8 minimal é necessário instalar explicitamente.
> Locale disponível após instalação: `pt_BR.utf8`

---

## 6. Diretórios dedicados

O pacote cria o usuário `postgres` automaticamente. Criar diretórios extras:

```bash
sudo mkdir -p /var/lib/pgsql/18/{backups,wal_archive}
sudo mkdir -p /var/log/postgresql
sudo chown -R postgres:postgres /var/lib/pgsql /var/log/postgresql
```

---

## 7. Inicializar cluster

```bash
sudo -u postgres /usr/pgsql-18/bin/initdb \
  -D /var/lib/pgsql/18/data \
  --encoding=UTF8 \
  --locale=pt_BR.utf8 \
  --data-checksums
```

> `--data-checksums` detecta corrupção silenciosa. Não pode ser ativado após o initdb — sempre incluir.
> Timezone detectado automaticamente: `America/Sao_Paulo`
> O `initdb` alerta sobre `trust` para conexões locais — corrigido no passo seguinte (pg_hba.conf).

---

## 8. postgresql.conf

```bash
cat >> /var/lib/pgsql/18/data/postgresql.conf <<'EOF'

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = '/var/log/postgresql'
log_filename = 'postgresql-%Y-%m-%d.log'
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_min_duration_statement = 1000

# Conexões
listen_addresses = 'localhost'
max_connections = 100

# Memória (ajustar conforme RAM da VM)
shared_buffers = 256MB
work_mem = 4MB
maintenance_work_mem = 64MB
EOF
```

---

## 9. pg_hba.conf

Substituir conteúdo padrão — sem `trust`, apenas `scram-sha-256`:

```bash
cat > /var/lib/pgsql/18/data/pg_hba.conf <<'EOF'
# TYPE  DATABASE  USER  ADDRESS         METHOD
local   all       postgres              peer
local   all       all                   scram-sha-256
host    all       all   127.0.0.1/32    scram-sha-256
host    all       all   ::1/128         scram-sha-256
EOF
```

---

## 10. Iniciar serviço

```bash
sudo systemctl enable --now postgresql-18
sudo systemctl status postgresql-18
```

---

## 11. Definir senha do superusuário

```bash
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'SenhaForte#2026';"
```

---

## 12. Verificar instalação

```bash
sudo -u postgres psql -c "SELECT version();"
```

Resultado obtido:
```
PostgreSQL 18.4 on x86_64-pc-linux-gnu, compiled by gcc (GCC) 8.5.0 20210514 (Red Hat 8.5.0-28), 64-bit
```

---

## 13. Firewall (pendente)

> O tutorial original configura `ufw` (Ubuntu). No OL8 o firewall é `firewalld`.
> **Não necessário enquanto `listen_addresses = 'localhost'`.**
> Executar somente ao permitir conexões externas:

```bash
sudo firewall-cmd --permanent --add-port=5432/tcp
sudo firewall-cmd --reload
sudo firewall-cmd --list-ports   # verificar
```

---

## Diferenças em relação ao tutorial original (PG16/Ubuntu)

| Item | Tutorial (Ubuntu) | Esta instalação (OL8) |
|------|------------------|-----------------------|
| Gerenciador de pacotes | `apt` | `dnf` |
| Repositório | apt.postgresql.org | pgdg-redhat-repo |
| Módulo AppStream | n/a | `dnf module disable postgresql` |
| Locale | pré-instalado | `glibc-langpack-pt` necessário |
| Nome do serviço | `postgresql` | `postgresql-18` |
| Firewall | `ufw` | `firewalld` |
| initdb manual | não realizado | sim (com checksums + locale) |
| pg_hba.conf | padrão | scram-sha-256 explícito |
