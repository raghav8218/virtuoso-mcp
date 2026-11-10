# virtuoso-mcp

An MCP server that connects AI assistants (Claude, Antigravity) to Cadence Virtuoso and Spectre.

It lets an AI assistant evaluate SKILL commands, check schematics, query transistor operating points from Spectre simulations, and export schematic PNGs directly through Cadence's native tools.

## Features

- **SKILL Execution**: Run arbitrary SKILL code headlessly in Virtuoso (`virtuoso -nograph -replay`).
- **Schematic Checks**: Run `schCheck` to catch opens, shorts, and floating nets.
- **Image Export**: Native `hiExportImage` rendering to 1080p PNG without third-party screenshot utilities.
- **Operating Point Queries**: Extract small-signal parameters ($g_m, g_{ds}, V_{th}, V_{dsat}$, region) directly from Spectre PSF databases.
- **Ocean Simulations**: Run analog testbenches via OCEAN batch scripts.
- **Local or SSH**: Works directly on a CAD Linux machine or connects over SSH from your laptop.

## Setup

```bash
git clone https://github.com/ISDL_UG_107/virtuoso-mcp.git
cd virtuoso-mcp
pip install -r requirements.txt
```

## Configuration

Copy `config.example.json` to `config.json` and set your paths:

```json
{
  "mode": "ssh",
  "ssh_host": "eda-uni",
  "ssh_port": 22,
  "ssh_user": "ISDL_UG_107",
  "ssh_key_path": null,
  "remote_work_dir": "/home/ISDL_UG_107/work",
  "cshrc_path": "/cad/cshrc",
  "default_library": "EE301_2026",
  "timeout": 60.0
}
```

*Set `"mode": "local"` if running directly on the Linux machine where Cadence is installed.*

## Connecting to Claude Desktop / Antigravity

Add this to your MCP configuration file (`claude_desktop_config.json` or `mcp_config.json`):

```json
{
  "mcpServers": {
    "virtuoso": {
      "command": "python",
      "args": ["F:/virtuoso-mcp/main.py"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

## Available Tools

| Tool | Description | Example |
|---|---|---|
| `get_status` | Check if Virtuoso is reachable | *(none)* |
| `eval_skill` | Run any SKILL code in Virtuoso | `code="plus(2 3)"` |
| `check_schematic` | Run `schCheck` on a cell | `cell="ssota"` |
| `export_schematic_image` | Export a schematic to PNG | `cell="ssota"`, `output_filename="ssota.png"` |
| `get_dc_operating_point` | Query $g_m, g_{ds}, V_{th}$ from Spectre results | `cell="ssota"`, `instance="M1"` |
| `run_spectre_simulation` | Run simulation via OCEAN | `cell="ssota"` |
| `run_terminal_command` | Run a shell command on the server | `command="ls -l"` |

## License

MIT
