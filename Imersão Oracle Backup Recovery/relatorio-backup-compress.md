# Relatório de Backup Comprimido — Comparação de Algoritmos RMAN

**Banco:** ORCL (DBID: 1761188099)
**Servidor:** ol8-dba.localdomain — 192.168.56.101
**Oracle Version:** 19.3.0.0.0
**Data da execução:** 16/05/2026
**Advanced Compression Option:** Habilitada (`v$option`)

---

## 1. Backups Executados

| Tag | Algoritmo | Comando |
|-----|-----------|---------|
| `FULL_DAILY` | Sem compressão (referência) | `BACKUP DATABASE PLUS ARCHIVELOG` |
| `COMPRESS_BASIC` | BASIC | `BACKUP AS COMPRESSED BACKUPSET ... TAG 'COMPRESS_BASIC'` |
| `COMPRESS_MEDIUM` | MEDIUM | `BACKUP AS COMPRESSED BACKUPSET ... TAG 'COMPRESS_MEDIUM'` |

---

## 2. Comparação de Resultados

Fonte: `v$rman_backup_job_details`

| Métrica | FULL_DAILY (sem compressão) | COMPRESS_BASIC | COMPRESS_MEDIUM |
|---------|:---------------------------:|:--------------:|:---------------:|
| Tamanho de entrada | 2,74 GB | 2,71 GB | 2,71 GB |
| Tamanho de saída | **2,19 GB** | **502 MB** | **443 MB** |
| Taxa de redução | 20,1% | **81,9%** | **84,0%** |
| Compression ratio | 1,25x | 5,52x | 6,26x |
| Duração | 41 s | 53 s | **20 s** |
| Status | COMPLETED | COMPLETED | COMPLETED |

> **MEDIUM foi mais rápido que BASIC neste lab.** Isso ocorre porque o MEDIUM usa um algoritmo (zlib) mais otimizado para CPUs modernas, enquanto o BASIC é otimizado para memória mínima — a diferença se inverte em DBs grandes com dados não comprimíveis.

---

## 3. Análise por Algoritmo

### FULL_DAILY — Sem compressão (baseline)
- Saída: 2,19 GB
- Redução de 20% ocorre naturalmente pelo RMAN (blocos vazios não são copiados — `unused block compression`)
- Nenhuma CPU extra consumida por compressão

### COMPRESS_BASIC
- Saída: **502 MB** — 81,9% menor que o input
- Algoritmo BZIP2 — sem licença adicional na Enterprise Edition
- Mais lento que MEDIUM por ser otimizado para uso mínimo de memória
- Cenário ideal: storage barato, CPU é o recurso escasso

### COMPRESS_MEDIUM
- Saída: **443 MB** — 84,0% menor que o input
- Algoritmo zlib — requer Advanced Compression Option
- Melhor equilíbrio CPU × espaço × tempo para a maioria dos cenários
- **Recomendado** para ambientes com licença disponível

---

## 4. Impacto na FRA

| Momento | Usado (GB) | % da FRA (10 GB) |
|---------|----------:|:----------------:|
| Antes (só FULL_DAILY) | 2,21 GB | 22,1% |
| Após BASIC + MEDIUM | 3,17 GB | 31,7% |
| Incremento dos dois backups comprimidos | ~0,96 GB | — |

Os dois backups comprimidos juntos ocuparam menos espaço que **metade** do backup original sem compressão (2,19 GB).

---

## 5. Algoritmos disponíveis — Referência rápida

| Algoritmo | Velocidade | Redução | CPU | Licença |
|-----------|:----------:|:-------:|:---:|---------|
| `BASIC` | Lenta | Alta | Alto | Enterprise Edition (sem add-on) |
| `LOW` | Muito rápida | Baixa | Baixo | Advanced Compression Option |
| `MEDIUM` | Equilibrada | Alta | Médio | Advanced Compression Option |
| `HIGH` | Muito lenta | Muito alta | Muito alto | Advanced Compression Option |

---

## 6. Configuração persistente recomendada

```rman
-- Definir MEDIUM como padrão permanente
CONFIGURE COMPRESSION ALGORITHM 'MEDIUM';
CONFIGURE DEVICE TYPE DISK BACKUP TYPE TO COMPRESSED BACKUPSET;

-- Verificar
SHOW COMPRESSION ALGORITHM;
SHOW DEVICE TYPE;
```

Para reverter ao comportamento sem compressão:
```rman
CONFIGURE COMPRESSION ALGORITHM CLEAR;
CONFIGURE DEVICE TYPE DISK BACKUP TYPE TO BACKUPSET;
```

---

## 7. Conclusão

| Item | Resultado |
|------|-----------|
| BASIC concluído | COMPLETED — 502 MB / 81,9% de redução |
| MEDIUM concluído | COMPLETED — 443 MB / 84,0% de redução |
| Algoritmo recomendado | **MEDIUM** (melhor ratio, mais rápido neste ambiente) |
| FRA após os três backups | 3,17 GB usados de 10 GB (31,7%) |
| Próximo passo sugerido | `recovery-full` — simular restore completo a partir destes backups |
