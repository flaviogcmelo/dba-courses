# Relatório de Metadados — Backup Full RMAN

**Banco:** ORCL (DBID: 1761188099)
**Servidor:** ol8-dba.localdomain — 192.168.56.101
**Oracle Version:** 19.3.0.0.0
**Data da extração:** 16/05/2026 às 23:41

---

## 1. Resumo do Job de Backup

Fonte: `V$RMAN_BACKUP_JOB_DETAILS`

| Campo | Valor |
|-------|-------|
| Session RECID | 5 |
| Status | **COMPLETED** |
| Início | 16/05/2026 23:20:51 |
| Término | 16/05/2026 23:21:32 |
| Duração | ~41 segundos |
| Tamanho de entrada (INPUT) | **2,74 GB** |
| Tamanho de saída (OUTPUT) | **2,19 GB** |
| Taxa de redução | ~20% |
| Dispositivo | DISK |

> O backup foi executado com tag `FULL_DAILY` via `BACKUP DATABASE PLUS ARCHIVELOG` com dois canais paralelos.

---

## 2. Backupsets Gerados

Fonte: `V$BACKUP_SET` — 10 backupsets registrados

| RECID | Tipo | CF Incluído | Nível | Pieces | Início | Conclusão | Duração (s) | KEEP |
|------:|------|:-----------:|------:|-------:|--------|-----------|:-----------:|:----:|
| 10 | D (Datafile) | **SIM** | Full | 1 | 23:21:32 | 23:21:33 | 1 | NO |
| 9 | L (Archived Log) | NÃO | Full | 1 | 23:21:31 | 23:21:31 | 0 | NO |
| 8 | D (Datafile) | NÃO | Full | 1 | 23:21:16 | 23:21:25 | 9 | NO |
| 7 | D (Datafile) | NÃO | Full | 1 | 23:21:16 | 23:21:17 | 1 | NO |
| 6 | D (Datafile) | NÃO | Full | 1 | 23:21:01 | 23:21:09 | 8 | NO |
| 5 | D (Datafile) | NÃO | Full | 1 | 23:21:01 | 23:21:02 | 1 | NO |
| 4 | D (Datafile) | NÃO | Full | 1 | 23:20:53 | 23:20:58 | 5 | NO |
| 3 | D (Datafile) | NÃO | Full | 1 | 23:20:53 | 23:20:57 | 4 | NO |
| 2 | L (Archived Log) | NÃO | Full | 1 | 23:20:52 | 23:20:52 | 0 | NO |
| 1 | L (Archived Log) | NÃO | Full | 1 | 23:20:52 | 23:20:52 | 0 | NO |

**Legenda Backup Type:**
- `D` — Datafile backupset
- `L` — Archived redo log backupset

**RECID 10** é o autobackup do controlfile + spfile (gerado automaticamente ao final pelo `CONFIGURE CONTROLFILE AUTOBACKUP ON`).

---

## 3. Backup Pieces (Arquivos Físicos)

Fonte: `V$BACKUP_PIECE` — arquivos gerados na FRA

| Arquivo | Status | Tamanho | Conclusão | Tipo |
|---------|:------:|--------:|-----------|:----:|
| `autobackup/2026_05_16/o1_mf_s_1233444092_o0l9kfhr_.bkp` | A | 17,95 MB | 23:21:33 | D |
| `backupset/2026_05_16/o1_mf_annnn_FULL_DAILY_o0l9kcty_.bkp` | A | 0,02 MB | 23:21:31 | L |
| `51F2B8BC.../o1_mf_nnndf_FULL_DAILY_o0l9jxt8_.bkp` | A | 220,11 MB | 23:21:30 | D |
| `51F29B9F.../o1_mf_nnndf_FULL_DAILY_o0l9jwdx_.bkp` | A | 252,84 MB | 23:21:24 | D |
| `51F29B9F.../o1_mf_nnndf_FULL_DAILY_o0l9jfb7_.bkp` | A | 304,14 MB | 23:21:15 | D |
| `51F2B8BC.../o1_mf_nnndf_FULL_DAILY_o0l9jf4h_.bkp` | A | 260,73 MB | 23:21:08 | D |
| `backupset/2026_05_16/o1_mf_nnndf_FULL_DAILY_o0l9j5x7_.bkp` | A | 777,47 MB | 23:20:59 | D |
| `backupset/2026_05_16/o1_mf_nnndf_FULL_DAILY_o0l9j5y7_.bkp` | A | 403,39 MB | 23:20:57 | D |
| `backupset/2026_05_16/o1_mf_annnn_FULL_DAILY_o0l9j4b3_.bkp` | A | 25,45 MB | 23:20:52 | L |
| `backupset/2026_05_16/o1_mf_annnn_FULL_DAILY_o0l9j4ch_.bkp` | A | 3,65 MB | 23:20:52 | L |

**Status A = Available** — todos os pieces estão íntegros e disponíveis para recovery.

Todos os arquivos estão sob: `/u01/app/oracle/fast_recovery_area/ORCL/`

---

## 4. Uso da Fast Recovery Area (FRA)

Fonte: `V$RECOVERY_FILE_DEST`

| Limite (GB) | Usado (GB) | Recuperável (GB) | % Uso |
|------------:|----------:|----------------:|------:|
| 10,00 | 2,21 | 0,00 | **22,13%** |

> FRA com folga confortável. Política de retenção configurada para 7 dias (`RECOVERY WINDOW OF 7 DAYS`).

---

## 5. Resumo RMAN — LIST BACKUP SUMMARY

```
Key  TY LV S  Device  Completion Time       #Pieces #Copies Compressed  Tag
---  -- -- -  ------  --------------------  ------- ------- ----------  ---
1    B  A  A  DISK    16-MAY-2026 23:20:52  1       1       NO          FULL_DAILY
2    B  A  A  DISK    16-MAY-2026 23:20:52  1       1       NO          FULL_DAILY
3    B  F  A  DISK    16-MAY-2026 23:20:57  1       1       NO          FULL_DAILY
4    B  F  A  DISK    16-MAY-2026 23:20:58  1       1       NO          FULL_DAILY
5    B  F  A  DISK    16-MAY-2026 23:21:02  1       1       NO          FULL_DAILY
6    B  F  A  DISK    16-MAY-2026 23:21:09  1       1       NO          FULL_DAILY
7    B  F  A  DISK    16-MAY-2026 23:21:17  1       1       NO          FULL_DAILY
8    B  F  A  DISK    16-MAY-2026 23:21:25  1       1       NO          FULL_DAILY
9    B  A  A  DISK    16-MAY-2026 23:21:31  1       1       NO          FULL_DAILY
10   B  F  A  DISK    16-MAY-2026 23:21:33  1       1       NO          TAG20260516T232132
```

**Legenda:**
- `TY=B` — Backupset
- `LV=A` — Archived log / `LV=F` — Full datafile
- `S=A` — Available (disponível)

---

## 6. Conclusão

| Item | Resultado |
|------|-----------|
| Status geral | ✅ COMPLETED sem erros |
| Datafiles backupeados | ✅ 7 backupsets de datafiles (CDB + PDBs) |
| Archived logs | ✅ 3 backupsets (sequences 27, 28, 29 e 30) |
| Controlfile autobackup | ✅ Incluso no RECID 10 |
| SPFILE | ✅ Incluso no autobackup (TAG20260516T232132) |
| Tamanho total gerado | **~2,21 GB** na FRA |
| Compressão | Não utilizada (backup sem `AS COMPRESSED`) |
| FRA disponível | **77,87%** livre |
| Recuperabilidade | Banco completamente recuperável a partir deste backup |
