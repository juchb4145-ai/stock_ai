# Sector/Theme Map Bootstrap Runbook

This project keeps the sector/theme gate in dry-run/log-only mode by default, but
empty maps still make every symbol fall back to `unknown`. Before the 2026-05-18
open, fill and validate these two files:

- `data/sector_map.csv`
- `data/theme_map.csv`

## Required Formats

`data/sector_map.csv`:

```csv
code,name,market,sector_code,sector_name,sector_index_code
005930,삼성전자,KOSPI,101,반도체,IDX101
000660,SK하이닉스,KOSPI,101,반도체,IDX101
```

Sector source input may also be JSON:

```json
{
  "101": {
    "sector_name": "반도체",
    "sector_index_code": "IDX101",
    "members": [
      {"code": "005930", "name": "삼성전자", "market": "KOSPI"},
      "000660"
    ]
  }
}
```

`data/theme_map.csv`:

```csv
theme_name,code,role
AI,005930,leader
AI,000660,member
```

Theme source input may also be JSON:

```json
{
  "AI": [
    {"code": "005930", "role": "leader"},
    "000660"
  ]
}
```

## Bootstrap From Local Exports

Export Kiwoom/local sector and theme data into the input shape above, then run:

```powershell
.\venv64\Scripts\python.exe tools\bootstrap_sector_theme_maps.py `
  --sector-source path\to\sector_source.csv `
  --theme-source path\to\theme_source.json `
  --sector-out data\sector_map.csv `
  --theme-out data\theme_map.csv `
  --fail-on-empty
```

Validate the current production maps without writing:

```powershell
.\venv64\Scripts\python.exe tools\bootstrap_sector_theme_maps.py --validate-only --fail-on-empty
```

Expected healthy output includes:

```text
sector_map status=ok path=data\sector_map.csv data_rows=... valid_rows=...
theme_map status=ok path=data\theme_map.csv data_rows=... valid_rows=...
```

## Startup Policy

Default startup policy is warn-only:

```powershell
$env:KIWOOM_SECTOR_THEME_MAP_POLICY="warn"
```

With `warn`, empty/header-only maps keep the existing dry-run unknown fallback,
but startup logs include `sector_map status=header_only` or
`theme_map status=header_only`.

Use fail-fast before the market open:

```powershell
$env:KIWOOM_SECTOR_THEME_MAP_POLICY="fail"
```

With `fail`, startup raises immediately if either map is missing, header-only, or
has no valid rows. This does not turn on sector/theme enforcement; it only
prevents silent all-unknown map startup. Gate enforcement remains controlled by:

- `KIWOOM_SECTOR_GATE_ENFORCEMENT_ENABLED`
- `KIWOOM_THEME_GATE_ENFORCEMENT_ENABLED`

## Build Fill-In Templates From Detection Logs

If no sector/theme source export is ready yet, generate fill-in templates from
the symbols that actually appeared in condition captures:

```powershell
.\venv64\Scripts\python.exe tools\bootstrap_sector_theme_maps.py `
  --template-from-condition-captures data\condition_captures.csv `
  --template-date 2026-05-18 `
  --sector-template-out reports\sector_theme_templates\20260518_sector_map_template.csv `
  --theme-template-out reports\sector_theme_templates\20260518_theme_map_template.csv
```

The template pre-fills code, name, market when available, first/last detected
time, detected count, and condition names. Fill `sector_code`,
`sector_name`, `sector_index_code`, `theme_name`, and `role`, then use the
same bootstrap command with `--sector-source` / `--theme-source` to write the
production maps.

When promoting a filled template, keep the source check enabled so partially
filled rows cannot be silently dropped:

```powershell
.\venv64\Scripts\python.exe tools\bootstrap_sector_theme_maps.py `
  --sector-source reports\sector_theme_templates\20260518_sector_map_template.csv `
  --theme-source reports\sector_theme_templates\20260518_theme_map_template.csv `
  --sector-out data\sector_map.csv `
  --theme-out data\theme_map.csv `
  --fail-on-empty `
  --fail-on-invalid-source
```
