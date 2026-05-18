---
name: backup-compress
description: Executar backup comprimido do banco Oracle 19c com RMAN, reduzindo espaço em disco usado pelos backupsets. Use sempre que o desafio envolver BACKUP AS COMPRESSED BACKUPSET, configurar algoritmo de compressão (BASIC, LOW, MEDIUM, HIGH), comparar taxa de compressão entre algoritmos, ou avaliar trade-off entre CPU e espaço em backup.
---

# Backup Comprimido com RMAN

## Objetivo

Executar backup com compressão para reduzir o tamanho dos backupsets em disco, escolhendo o algoritmo adequado ao trade-off CPU × espaço × tempo.

## Pré-requisitos

- Skill `backup-full` aplicada (RMAN configurado, FRA, archivelog)
- Acesso `SYSDBA` ou role `SYSBACKUP`
- Para algoritmos `LOW`, `MEDIUM` e `HIGH`: licença **Advanced Compression Option**
- Algoritmo `BASIC` é incluído na Enterprise Edition sem licença adicional

## Algoritmos de compressão

| Algoritmo | Velocidade | Taxa | CPU | Licença |
|-----------|-----------|------|-----|---------|
| `BASIC` | Lenta | Alta | Alto | Enterprise (sem add-on) |
| `LOW` | Muito rápida | Baixa | Baixo | Advanced Compression |
| `MEDIUM` | Equilibrada | Média | Médio | Advanced Compression |
| `HIGH` | Muito lenta | Muito alta | Muito alto | Advanced Compression |

Regra prática: **`MEDIUM` é o ponto de equilíbrio** para a maioria dos cenários quando a licença está disponível. Sem licença, use `BASIC`.

## Passo a passo

### 1. Verificar algoritmo atual configurado

```rman
SHOW COMPRESSION ALGORITHM;
```

### 2. Definir o algoritmo persistentemente

```rman
CONFIGURE COMPRESSION ALGORITHM 'MEDIUM';
```

Outras opções: `'BASIC'`, `'LOW'`, `'HIGH'`.

### 3. Executar backup comprimido

**Forma persistente (todos os backups comprimidos):**
```rman
CONFIGURE DEVICE TYPE DISK BACKUP TYPE TO COMPRESSED BACKUPSET;
BACKUP DATABASE PLUS ARCHIVELOG;
```

**Forma pontual (só este backup):**
```rman
BACKUP AS COMPRESSED BACKUPSET DATABASE PLUS ARCHIVELOG;
```

**Com tag e canais:**
```rman
RUN {
  ALLOCATE CHANNEL c1 DEVICE TYPE DISK;
  ALLOCATE CHANNEL c2 DEVICE TYPE DISK;
  BACKUP AS COMPRESSED BACKUPSET
    TAG 'FULL_COMPRESSED'
    DATABASE PLUS ARCHIVELOG;
  RELEASE CHANNEL c1;
  RELEASE CHANNEL c2;
}
```

### 4. Comparar algoritmos (exercício prático recomendado)

Execute em sequência e compare tamanhos:

```rman
BACKUP AS COMPRESSED BACKUPSET TAG 'TEST_BASIC'  DATABASE;
-- alterar algoritmo
CONFIGURE COMPRESSION ALGORITHM 'LOW';
BACKUP AS COMPRESSED BACKUPSET TAG 'TEST_LOW'    DATABASE;
CONFIGURE COMPRESSION ALGORITHM 'MEDIUM';
BACKUP AS COMPRESSED BACKUPSET TAG 'TEST_MEDIUM' DATABASE;
CONFIGURE COMPRESSION ALGORITHM 'HIGH';
BACKUP AS COMPRESSED BACKUPSET TAG 'TEST_HIGH'   DATABASE;
```

## Validação

```rman
-- Comparar tamanho de entrada vs saída
LIST BACKUP SUMMARY;
```

Em SQL*Plus — comparar taxa de compressão por tag:
```sql
SELECT b.tag,
       ROUND(SUM(b.bytes)/1024/1024, 2)              AS backup_mb,
       ROUND(SUM(b.original_input_bytes)/1024/1024, 2) AS input_mb,
       ROUND( (1 - SUM(b.bytes)/SUM(b.original_input_bytes)) * 100, 2) AS ratio_pct
FROM   v$backup_piece b
WHERE  b.tag LIKE 'TEST_%'
GROUP  BY b.tag
ORDER  BY b.tag;
```

```sql
-- Detalhar tempo gasto
SELECT session_recid, input_type, compression_ratio,
       time_taken_display, output_bytes_display
FROM   v$rman_backup_job_details
ORDER  BY start_time DESC
FETCH  FIRST 10 ROWS ONLY;
```

## Troubleshooting

| Erro | Causa provável | Solução |
|------|----------------|---------|
| `ORA-19918: Advanced Compression Option required` | Tentou usar LOW/MEDIUM/HIGH sem licença | Usar `BASIC` ou licenciar a feature |
| Backup mais lento que o normal | CPU saturada pela compressão | Reduzir paralelismo ou trocar para algoritmo mais leve (`LOW`) |
| Taxa de compressão baixa em dados já comprimidos | Banco já contém LOBs/BLOBs comprimidos ou tabelas com Advanced Compression | Normal — dados já comprimidos não comprimem mais |

## Reverter para backup sem compressão

```rman
CONFIGURE COMPRESSION ALGORITHM CLEAR;
CONFIGURE DEVICE TYPE DISK BACKUP TYPE TO BACKUPSET;
```
