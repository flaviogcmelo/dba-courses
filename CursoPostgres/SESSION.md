# Handoff — Curso PostgreSQL

> Última sessão: 2026-06-28 | Continuar em: 2026-06-29

---

## Ambiente

| Item | Valor |
|------|-------|
| VM de treino | `192.168.56.21` (VirtualBox, host-only) |
| OS | Oracle Linux 8.10 |
| PostgreSQL | 18.4 |
| Acesso SSH | `ssh root@192.168.56.21` (chave `~/.ssh/id_ed25519`) |
| PGDATA | `/var/lib/pgsql/18/data/` |
| Logs | `/var/log/postgresql/` |
| Serviço | `systemctl {start|stop|restart|status} postgresql-18` |
| Senha postgres | `SenhaForte#2026` |

---

## O que foi feito

### Instalação (Seção 1)
- Repo PGDG instalado, módulo AppStream desabilitado
- `glibc-langpack-pt` instalado (locale `pt_BR.utf8`)
- `initdb` com `--data-checksums --encoding=UTF8 --locale=pt_BR.utf8`
- `postgresql.conf` configurado (logging, memória, conexões)
- `pg_hba.conf` configurado com `scram-sha-256` (sem `trust`)
- Serviço habilitado e rodando
- **Arquivo:** `CursoPostgres/instalacao-postgres18-ol8.md`

### Arquitetura (Seção 1 — teoria)
- Notas de processos (postmaster, backend, background), memória (shared/local), novidades PG18
- **Arquivo:** `CursoPostgres/secao1-arquitetura-postgres18.md`

### Acesso Remoto (Seção 2)
- `firewall-cmd --permanent --add-port=5432/tcp` executado
- `listen_addresses = '*'` em postgresql.conf — PostgreSQL escuta em todas as interfaces
- Serviço restartado — confirmado com `ss -tlnp | grep 5432`
- **Arquivo:** `CursoPostgres/secao2-acesso-remoto.md`

---

## Próximo passo

**Seção 2 — próxima aula: pg_hba.conf**

O professor vai explicar os métodos de autenticação. Nosso `pg_hba.conf` atual já está configurado com `scram-sha-256`, mas a aula vai detalhar as opções (trust, md5, scram-sha-256, peer, ident, reject) e quando usar cada uma.

Arquivo atual em `/var/lib/pgsql/18/data/pg_hba.conf`:

```
local   all       postgres              peer
local   all       all                   scram-sha-256
host    all       all   127.0.0.1/32    scram-sha-256
host    all       all   ::1/128         scram-sha-256
```

Falta adicionar regra para **conexões remotas** (host com IP da rede), que será tema da aula.

---

## Como retomar

```bash
# 1. No PC do trabalho — atualizar o repo
git -C <caminho>/dba-courses pull

# 2. Verificar se a VM está acessível
ssh root@192.168.56.21 "systemctl status postgresql-18 --no-pager | head -5"

# 3. Continuar anotações no Obsidian
# D:\Users\OneDrive\Documentos\ObsidianVault\01-Projetos\Profissional\CursoPostgres\

# 4. Ao criar nova nota — copiar para o repo e commitar
Copy-Item "<obsidian-path>\<arquivo>.md" "dba-courses\CursoPostgres\<arquivo>.md"
git -C dba-courses add CursoPostgres/<arquivo>.md
git -C dba-courses commit -m "docs: ..."
git -C dba-courses push
```

---

## Arquivos do curso no repo

```
CursoPostgres/
├── instalacao-postgres18-ol8.md   ✅ commitado
├── secao1-arquitetura-postgres18.md  ✅ commitado
├── secao2-acesso-remoto.md        ✅ commitado
└── SESSION.md                     ← este arquivo
```
