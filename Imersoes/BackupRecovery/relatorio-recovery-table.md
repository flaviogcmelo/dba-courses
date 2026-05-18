# Relatório de Recovery — Flashback Table: HR.COUNTRIES

**Banco:** ORCL / PDB: ORCLPDB (DBID: 1761188099)
**Servidor:** ol8-dba.localdomain — 192.168.56.101
**Oracle Version:** 19.3.0.0.0
**Schema:** HR (Human Resources)
**Tabela recuperada:** `HR.COUNTRIES`
**Data do incidente:** 17/05/2026 às 10:12:17
**Data do recovery:** 17/05/2026
**Método:** FLASHBACK TABLE TO BEFORE DROP (Recycle Bin)

---

## 1. Resumo Executivo

| Item | Detalhe |
|------|---------|
| **Natureza do incidente** | DROP acidental da tabela `HR.COUNTRIES` |
| **Método de recovery** | `FLASHBACK TABLE HR.COUNTRIES TO BEFORE DROP` |
| **Backup RMAN necessário** | Não — uso exclusivo do Recycle Bin |
| **Instância auxiliar necessária** | Não — operação in-place |
| **Tempo de recovery** | Segundos |
| **Perda de dados** | **Zero** — todos os 25 registros recuperados |
| **Status final** | Tabela operacional em `ORCLPDB` |

---

## 2. Distinção entre Flashback Table e RMAN RECOVER TABLE

Esta skill utilizou o **Flashback Table via Recycle Bin** — diferente do **RMAN RECOVER TABLE** documentado na skill `recovery-table`:

| Característica | Flashback Table (TO BEFORE DROP) | RMAN RECOVER TABLE |
|----------------|----------------------------------|-------------------|
| **Mecanismo** | Recycle Bin | Backup RMAN + instância auxiliar |
| **Velocidade** | Segundos | Minutos a horas |
| **Pré-requisito** | Tabela não dropada com `PURGE` | Backup RMAN + archivelogs |
| **Backup necessário** | Não | Sim |
| **Impacto no banco** | Zero | Criação de instância auxiliar |
| **Caso de uso** | DROP sem PURGE recente | DROP com PURGE, retenção de undo expirada |

> A skill `recovery-table` (RMAN RECOVER TABLE) é usada quando o Flashback Table **não cobre o cenário** — ex: tabela dropada com `PURGE` ou undo já expirado.

---

## 3. Diagnóstico do Incidente

### 3.1 Estado antes do recovery

```
ORA-00942: table or view does not exist
-- HR.COUNTRIES inacessível no ORCLPDB
```

### 3.2 Recycle Bin — objetos identificados

| OBJECT_NAME (BIN$) | ORIGINAL_NAME | TYPE | DROPTIME |
|--------------------|---------------|------|----------|
| `BIN$UgQx/hRCr+rgY2U4qMBwFg==$0` | COUNTRIES | TABLE | 2026-05-17 10:12:17 |
| `BIN$UgQx/hRBr+rgY2U4qMBwFg==$0` | COUNTRY_C_ID_PK | IOT TOP Index | 2026-05-17 10:12:17 |

A tabela foi encontrada intacta no Recycle Bin — DROP executado **sem a cláusula `PURGE`**, o que preservou os objetos e tornou o Flashback Table possível.

---

## 4. Processo de Recovery

### 4.1 Conexão no container correto

```sql
ALTER SESSION SET CONTAINER = orclpdb;
```

### 4.2 Comando de recovery

```sql
FLASHBACK TABLE hr.countries TO BEFORE DROP;
-- Flashback complete.
```

Execução instantânea — o Oracle restaurou a tabela diretamente do Recycle Bin, sem necessidade de restore de backup ou instância auxiliar.

---

## 5. Validação Pós-Recovery

### 5.1 Tabela restaurada

```
TABLE_NAME   ROW_MOVEMENT   NUM_ROWS
------------ -------------- --------
COUNTRIES    DISABLED        25
```

### 5.2 Dados recuperados — todos os 25 países

| COUNTRY_ID | COUNTRY_NAME | REGION_ID |
|:----------:|--------------|:---------:|
| AR | Argentina | 20 |
| AU | Australia | 40 |
| BE | Belgium | 10 |
| BR | Brazil | 20 |
| CA | Canada | 20 |
| CH | Switzerland | 10 |
| CN | China | 30 |
| DE | Germany | 10 |
| DK | Denmark | 10 |
| EG | Egypt | 50 |
| FR | France | 10 |
| GB | United Kingdom of Great Britain and Northern Ireland | 10 |
| IL | Israel | 30 |
| IN | India | 30 |
| IT | Italy | 10 |
| JP | Japan | 30 |
| KW | Kuwait | 30 |
| ML | Malaysia | 30 |
| MX | Mexico | 20 |
| NG | Nigeria | 50 |
| NL | Netherlands | 10 |
| SG | Singapore | 30 |
| US | United States of America | 20 |
| ZM | Zambia | 50 |
| ZW | Zimbabwe | 50 |

**25 de 25 registros recuperados — zero perda de dados.**

### 5.3 Constraints recuperadas

| CONSTRAINT_NAME | TIPO | STATUS | Observação |
|----------------|------|--------|------------|
| `BIN$UgQx/hQ/r+rgY2U4qMBwFg==$0` | C (Check) | ENABLED | Nome com prefixo BIN$ |
| `BIN$UgQx/hRAr+rgY2U4qMBwFg==$0` | P (Primary Key) | ENABLED | Nome com prefixo BIN$ |

### 5.4 Recycle Bin após recovery

```
no rows selected — Recycle Bin vazio
```

---

## 6. Ação Pós-Recovery Recomendada — Renomear Constraints

Comportamento esperado do Flashback Table: as constraints são recuperadas com os nomes `BIN$` do Recycle Bin. Para restaurar os nomes originais:

```sql
ALTER SESSION SET CONTAINER = orclpdb;

-- Renomear Primary Key
ALTER TABLE hr.countries
  RENAME CONSTRAINT "BIN$UgQx/hRAr+rgY2U4qMBwFg==$0"
  TO country_c_id_pk;

-- Renomear Check Constraint
ALTER TABLE hr.countries
  RENAME CONSTRAINT "BIN$UgQx/hQ/r+rgY2U4qMBwFg==$0"
  TO country_c_id_ck;
```

---

## 7. Timeline do Incidente

| Horário | Evento |
|---------|--------|
| 17/05/2026 10:12:17 | `DROP TABLE hr.countries` executado (sem PURGE) |
| 17/05/2026 ~10:12 | Tabela movida para o Recycle Bin automaticamente pelo Oracle |
| 17/05/2026 (sessão) | Diagnóstico: tabela ausente detectada; Recycle Bin consultado |
| 17/05/2026 (sessão) | `FLASHBACK TABLE hr.countries TO BEFORE DROP` executado |
| 17/05/2026 (sessão) | **Recovery concluído** — 25 registros, 2 constraints restaurados |

---

## 8. Conclusão

| Critério | Resultado |
|----------|-----------|
| Tabela recuperada | ✅ SIM |
| Perda de dados | ✅ ZERO — 25/25 registros |
| Constraints ativas | ✅ SIM (renomear BIN$ recomendado) |
| Recycle Bin limpo | ✅ SIM |
| Backup RMAN necessário | ✅ NÃO — Recycle Bin suficiente |
| Tempo de recovery | ✅ Segundos |

---

## 9. Quando usar cada abordagem

```
DROP TABLE executado?
        │
        ├── COM PURGE ou undo expirado?
        │       └── SIM → RMAN RECOVER TABLE (skill recovery-table)
        │                  Restore via backup + instância auxiliar
        │
        └── SEM PURGE (recente)?
                └── SIM → FLASHBACK TABLE ... TO BEFORE DROP (este relatório)
                           Restore via Recycle Bin — segundos, sem backup
```

---

## 10. Referências

- Skill utilizada: `recovery-table` — `D:\work\dba-courses\Imersoes\BackupRecovery\skills\recovery-table\SKILL.md`
- Oracle Documentation: [FLASHBACK TABLE Statement](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/FLASHBACK-TABLE.html)
- Oracle Documentation: [Managing the Recycle Bin](https://docs.oracle.com/en/database/oracle/oracle-database/19/admin/managing-tables.html#GUID-4C0F2D4F-9A84-4E45-B7F3-B7F4F0D0F7A2)
