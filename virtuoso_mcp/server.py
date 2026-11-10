import os
from typing import Optional
from mcp.server.fastmcp import FastMCP
from .config import VirtuosoConfig
from .executor import get_executor
from .skill_helpers import (
    build_sch_check_script,
    build_export_schematic_script,
    build_dc_operating_point_script,
    build_ocean_simulation_script,
)

mcp = FastMCP("Virtuoso-MCP")
config = VirtuosoConfig.load()
executor = get_executor(config)

@mcp.tool()
def get_status() -> str:
    """Check if Virtuoso is available and print environment details."""
    code, out, err = executor.run_command("which virtuoso && uname -a")
    status = "CONNECTED" if code == 0 and "virtuoso" in out else "UNAVAILABLE"
    return f"""Status: {status}
Mode: {config.mode}
Host: {config.ssh_host if config.mode == 'ssh' else 'localhost'}
WorkDir: {config.remote_work_dir}
Binary: {out.strip() if code == 0 else err.strip()}
"""

@mcp.tool()
def eval_skill(code: str, timeout: Optional[float] = None) -> str:
    """Run any SKILL command inside Virtuoso and return stdout."""
    return executor.execute_skill(code, timeout=timeout)

@mcp.tool()
def check_schematic(cell: str, lib: Optional[str] = None, view: str = "schematic") -> str:
    """Run schCheck on a schematic. Returns (warnings errors)."""
    target_lib = lib or config.default_library
    return executor.execute_skill(build_sch_check_script(target_lib, cell, view))

@mcp.tool()
def export_schematic_image(
    cell: str,
    lib: Optional[str] = None,
    view: str = "schematic",
    output_filename: str = "schematic.png",
    width: int = 1920,
    height: int = 1080,
    download_to_local: bool = True
) -> str:
    """Export a schematic to PNG using hiExportImage and optionally pull it to local disk."""
    target_lib = lib or config.default_library
    remote_png = f"{config.remote_work_dir}/{output_filename}" if not output_filename.startswith("/") else output_filename
    
    skill = build_export_schematic_script(target_lib, cell, view, remote_png, width, height)
    result = executor.execute_skill(skill)
    
    local_info = ""
    if download_to_local and "SUCCESS" in result:
        local_dest = os.path.join(os.getcwd(), os.path.basename(output_filename))
        if executor.pull_file(remote_png, local_dest):
            local_info = f"\nSaved to: {local_dest}"
            
    return f"{result}{local_info}"

@mcp.tool()
def get_dc_operating_point(cell: str, instance: str, results_dir: Optional[str] = None) -> str:
    """Read transistor DC operating point parameters (gm, gds, vth, vdsat, region) from Spectre results."""
    target_results = results_dir or f"{config.remote_work_dir}/simulation/{cell}/spectre/schematic/psf"
    return executor.execute_skill(build_dc_operating_point_script(target_results, instance))

@mcp.tool()
def run_spectre_simulation(cell: str, lib: Optional[str] = None, view: str = "schematic", ocean_commands: str = "") -> str:
    """Netlist and run a simulation with Spectre using an OCEAN script."""
    target_lib = lib or config.default_library
    skill = build_ocean_simulation_script(target_lib, cell, view, ocean_commands)
    return executor.execute_skill(skill)

@mcp.tool()
def run_terminal_command(command: str, timeout: Optional[float] = None) -> str:
    """Run a shell command on the Cadence server."""
    code, stdout, stderr = executor.run_command(command, timeout=timeout)
    out = [f"Exit Status: {code}"]
    if stdout.strip():
        out.append(f"STDOUT:\n{stdout.strip()}")
    if stderr.strip():
        out.append(f"STDERR:\n{stderr.strip()}")
    return "\n\n".join(out)

def main():
    mcp.run()

if __name__ == "__main__":
    main()
