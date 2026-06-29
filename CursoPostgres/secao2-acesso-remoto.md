# Seção 2 — Configuração de Acesso Remoto

> Curso Udemy — PostgreSQL | Notas da Seção 2
> Executado em: 2026-06-28 | VM: 192.168.56.21 (OL8.10 / PG 18.4)

---

## Conceito

Por padrão, o PostgreSQL **não escuta conexões remotas** — aceita apenas conexões locais (loopback `127.0.0.1`). Para habilitar acesso remoto são necessários dois passos:

1. **Firewall** — abrir a porta 5432
2. **postgresql.conf** — alterar `listen_addresses`

> O pg_hba.conf controla **autenticação** (quem pode conectar e como) — tema da próxima aula.

---

## Passo 1 — Firewall

### Curso (Ubuntu/AWS)
O curso usa AWS EC2 com **Security Groups** — equivalente a um firewall de rede. A regra adicionada foi TCP 5432 de qualquer origem (`0.0.0.0/0`).

### Nossa VM (OL8 — firewalld)

```bash
# Abrir porta 5432 permanentemente
firewall-cmd --permanent --add-port=5432/tcp
firewall-cmd --reload

# Verificar
firewall-cmd --list-ports
```

Resultado: `5432/tcp`

> Em produção: restringir a origem aos IPs específicos das aplicações, não `0.0.0.0/0`.

---

## Passo 2 — listen_addresses no postgresql.conf

### Por que isso existe?

O parâmetro define **em quais interfaces de rede** o PostgreSQL aceita conexões. Um servidor pode ter múltiplas interfaces (storage, backup, replicação) — permite separar o tráfego de banco de dados das demais.

### Valores possíveis

| Valor | Comportamento |
|-------|--------------|
| `localhost` | Somente conexões locais (padrão após nossa instalação) |
| `*` | Todas as interfaces do servidor |
| `192.168.56.21` | Interface específica |
| `192.168.56.21, 10.0.0.1` | Múltiplas interfaces específicas |

### Alteração realizada

Arquivo: `/var/lib/pgsql/18/data/postgresql.conf`

```bash
# Antes
listen_addresses = 'localhost'

# Depois
listen_addresses = '*'
```

> Usamos `*` porque o IP da VM VirtualBox pode mudar. Em produção, preferir IPs fixos explícitos.

### Aplicar a mudança (restart obrigatório)

```bash
systemctl restart postgresql-18
systemctl status postgresql-18
```

> `listen_addresses` exige **restart** (não apenas reload) — altera o socket de escuta do processo.

### Verificar resultado

```bash
ss -tlnp | grep 5432
```

Saída esperada:
```
LISTEN 0  200  0.0.0.0:5432  0.0.0.0:*  users:(("postgres",...))
LISTEN 0  200     [::]:5432     [::]:*  users:(("postgres",...))
```

`0.0.0.0` = todas as interfaces IPv4 | `[::]` = todas as interfaces IPv6.

---

## Diferenças curso vs nossa instalação

| Item | Curso (Ubuntu/AWS) | Nossa VM (OL8/VirtualBox) |
|------|-------------------|--------------------------|
| Firewall | AWS Security Group | `firewalld` |
| Comando firewall | Console AWS web | `firewall-cmd --permanent` |
| Restrição de origem | Qualquer (teste) | Qualquer (teste) |
| Arquivo conf | `/etc/postgresql/16/main/postgresql.conf` | `/var/lib/pgsql/18/data/postgresql.conf` |
| Restart | `systemctl restart postgresql` | `systemctl restart postgresql-18` |

---

## Próxima aula

Configuração do **pg_hba.conf** — controle de autenticação (quem pode conectar, de onde e com qual método).
