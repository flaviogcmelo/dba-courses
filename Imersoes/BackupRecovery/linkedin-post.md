# Post LinkedIn — Imersão Oracle Backup & Recovery

> **Instruções de publicação:**
> - Cole o texto abaixo diretamente no LinkedIn
> - Anexe as imagens na ordem indicada pelos marcadores 📸
> - Remova as linhas de instrução em itálico com 📸 antes de publicar

---

## TEXTO DO POST

Hoje foi mais um dia de mão na massa e estudo voltado para Oracle 19c Backup & Recovery — em um banco recém-instalado ao backup comprimido, com dados reais saindo do terminal.

---

🔧 **Fase 1 — Preparação do ambiente**

Parti de um Oracle 19c Enterprise Edition zerado numa VM Oracle Linux 8.10. Antes de qualquer backup, três configurações são obrigatórias:

**Fast Recovery Area (FRA)**
Destino centralizado de 10 GB para backupsets, archivelogs e autobackup do controlfile. Tudo em um lugar só, gerenciado automaticamente pelo Oracle.

**Modo ARCHIVELOG**
Sem isso não existe backup online consistente. O banco passou de NOARCHIVELOG para ARCHIVELOG — e os primeiros archivelogs já foram gravados automaticamente na FRA.

📸 *[Inserir: 01-habilitarFRA.jpeg — tabela antes/depois: Log mode NOARCHIVELOG → ARCHIVELOG, Automatic archival Disabled → Enabled]*

**Flashback Database**
Habilitei o Flashback para permitir "voltar no tempo" sem restore completo. É a diferença entre um incidente de 2 horas e um incidente de 2 minutos.

📸 *[Inserir: 02-habilitarArchive.jpeg — confirmação das duas skills concluídas: habilitar-fra ✅ habilitar-archivelog ✅]*

---

🗃️ **Fase 2 — Schema de exemplo**

Instalei o schema HR da Oracle no PDB ORCLPDB — 7 tabelas (107 funcionários, 27 departamentos, 25 países, entre outros), 1 view, 11 índices, procedures, triggers e sequences, todos os dados populados e validados. Ele vai ser o alvo dos cenários de recovery nas próximas sessões — restore completo, recuperação de tabela e DUPLICATE.

📸 *[Inserir: 03-schemaHR.jpeg — schema HR instalado no ORCLPDB: 7 tabelas (regions, countries, departments, locations, employees, jobs, job_history) com todos os registros validados ✅, incluindo 107 funcionários, 1 view e 11 índices]*

---

💾 **Fase 3 — Backup com RMAN**

Executei três backups do mesmo banco para comparar performance e compressão:

**1. Backup full sem compressão (referência)**
→ Entrada: 2,74 GB | Saída: 2,19 GB
→ Redução de 20% — apenas pelo unused block compression nativo do RMAN
→ 10 backupsets gerados: datafiles do CDB, PDB$SEED, ORCLPDB, archivelogs + autobackup do controlfile/spfile
→ Duração: 41 segundos | Status: COMPLETED

📸 *[Inserir: 04-backupFull.jpeg — resultado do backup full com todas as métricas e validação REPORT NEED BACKUP + REPORT OBSOLETE limpos]*

**2. Backup comprimido BASIC**
→ Entrada: 2,71 GB | Saída: 502 MB
→ Redução de 82% 🔥 | Duração: 53 segundos
→ Disponível na Enterprise Edition sem licença adicional

**3. Backup comprimido MEDIUM** *(Advanced Compression Option)*
→ Entrada: 2,71 GB | Saída: 443 MB
→ Redução de 84% 🔥 | Duração: 20 segundos

📸 *[Inserir: 05-backupComparacaoCompressao.jpeg — tabela comparativa dos três backups: saída, redução e tempo lado a lado]*

---

💡 **O resultado que me surpreendeu**

MEDIUM foi mais rápido que BASIC — 20 segundos contra 53 segundos.

Em teoria o BASIC deveria ser mais simples e veloz. O que acontece na prática: MEDIUM usa zlib, muito mais otimizado para CPUs modernas. BASIC usa BZIP2, projetado para consumo mínimo de memória — não para velocidade.

Em ambientes com dados heterogêneos ou hardware mais antigo, o BASIC pode se sair melhor. Mas com CPUs recentes, MEDIUM é o ponto de equilíbrio ideal entre espaço e performance.

---

🤖 **Sobre o processo**

Todo o lab foi conduzido com **Claude Code** como copiloto — scripts RMAN, queries em `V$BACKUP_SET`, `V$BACKUP_PIECE` e `V$RMAN_BACKUP_JOB_DETAILS`, relatórios em Markdown gerados direto do terminal. Produtividade de outro nível para quem trabalha sozinho num lab.

---

📌 **Próximas sessões**
- Restore completo + recover
- RMAN RECOVER TABLE (recuperação granular sem restore total)
- RMAN DUPLICATE — clonar o banco para outro servidor

---

Se você trabalha com Oracle: qual algoritmo usa na sua estratégia de backup? BASIC, MEDIUM — ou ainda vai de fita? 👇

---

#OracleDatabase #OracleDBA #DBA #RMAN #Backup #Oracle19c #BackupAndRecovery #DatabaseAdministration #Linux #OracleLinux #TechBrasil #BancoDeDados
