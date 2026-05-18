# Oracle Backup & Recovery — Skills da Imersão

Pacote de 8 skills para uma imersão prática em **Oracle Database 19c Single Instance**, cobrindo do preparo do ambiente até cenários complexos de recovery.

## Estrutura

```
oracle-backup-recovery-skills/
├── habilitar-fra/SKILL.md           # 1. Fast Recovery Area
├── habilitar-archivelog/SKILL.md    # 2. Modo ARCHIVELOG
├── configure-flashback/SKILL.md     # 3. Flashback Database
├── backup-full/SKILL.md             # 4. Backup full com RMAN
├── backup-compress/SKILL.md         # 5. Backup comprimido
├── recovery-full/SKILL.md           # 6. Restore + recover completo
├── recovery-table/SKILL.md          # 7. RMAN RECOVER TABLE
└── duplicate/SKILL.md               # 8. RMAN DUPLICATE DATABASE
```

> **Importante**: o nome da pasta de cada skill é idêntico ao campo `name:` no YAML frontmatter. Os prefixos numéricos foram removidos para evitar conflitos com o resolver do Claude Code.

## Sequência didática sugerida

**Fase 1 — Preparação do ambiente**
1. `habilitar-fra`
2. `habilitar-archivelog`
3. `configure-flashback`

**Fase 2 — Backup**
4. `backup-full`
5. `backup-compress`

**Fase 3 — Recovery**
6. `recovery-full`
7. `recovery-table`
8. `duplicate`

## Como instalar no Claude Code

### Instalação pessoal (recomendado para a imersão)

```bash
mkdir -p ~/.claude/skills
unzip oracle-backup-recovery-skills.zip -d /tmp/
cp -r /tmp/oracle-backup-recovery-skills/{habilitar-fra,habilitar-archivelog,configure-flashback,backup-full,backup-compress,recovery-full,recovery-table,duplicate} ~/.claude/skills/
```

Verificar:
```bash
ls ~/.claude/skills/habilitar-fra/SKILL.md
# Deve existir
```

Reiniciar o Claude Code e checar:
```
/skills
```

### Instalação por projeto (versionada no git)

```bash
cd ~/meu-projeto-imersao
mkdir -p .claude/skills
cp -r /tmp/oracle-backup-recovery-skills/{habilitar-fra,habilitar-archivelog,configure-flashback,backup-full,backup-compress,recovery-full,recovery-table,duplicate} .claude/skills/
git add .claude/skills/
git commit -m "Skills da imersão Oracle Backup & Recovery"
```

## Como usar as skills

### Por linguagem natural (funciona sempre)

Basta pedir ao Claude Code mencionando o tema. Ele lê a `description` da skill e carrega o `SKILL.md` automaticamente:

```
Preciso habilitar a FRA num Oracle 19c Single Instance, me ajude passo a passo
```

```
Me guie na configuração do Flashback Database
```

```
Quero fazer um backup full comprimido com RMAN
```

### Invocando a skill pelo nome

```
Use a skill habilitar-fra
```

```
Aplique a skill recovery-table para recuperar HR.EMPLOYEES até as 14h de hoje
```

### Slash commands

Em versões recentes do Claude Code, slash commands como `/habilitar-fra` devem funcionar. Se receber `Unknown skill: <nome>`:

1. Confirme que a pasta está em `~/.claude/skills/<nome>/SKILL.md` (sem nível extra de aninhamento).
2. Confirme que o `name:` no YAML bate exatamente com o nome da pasta.
3. Reinicie o Claude Code com mais headroom para descriptions:
   ```bash
   SLASH_COMMAND_TOOL_CHAR_BUDGET=30000 claude
   ```
4. Como fallback, use linguagem natural — funciona em qualquer versão.

## Padrão de cada SKILL.md

Todas seguem a mesma estrutura:

- **YAML frontmatter** (`name`, `description`)
- **Objetivo**
- **Pré-requisitos**
- **Passo a passo** (SQL*Plus / RMAN / bash)
- **Validação**
- **Troubleshooting** (tabela erro / causa / solução)
- **Rollback / Limpeza**

## Ambiente alvo

- Oracle Database **19c**
- **Single Instance** (não-RAC)
- Non-CDB (adaptável para CDB/PDB)
- Linux (paths em `/u01/app/oracle/...`)
