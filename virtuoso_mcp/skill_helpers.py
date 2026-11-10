def wrap_skill(code: str, output_file: str = "_mcp_output.txt") -> str:
    # wrap in errset so syntax errors don't hang virtuoso in batch mode
    return f"""
let((p res)
  p = outfile("{output_file}")
  res = errset({code.strip()})
  if(res then
    fprintf(p "SUCCESS: %L\\n" car(res))
  else
    fprintf(p "ERROR: %s\\n" car(errset.lastErrorText))
  )
  close(p)
)
exit()
"""

def build_sch_check_script(lib: str, cell: str, view: str = "schematic") -> str:
    return f"""
let((cv res)
  cv = dbOpenCellViewByType("{lib}" "{cell}" "{view}" "schematic" "a")
  if(cv then
    res = schCheck(cv)
    dbSave(cv)
    dbClose(cv)
    res
  else
    list("ERROR" "CellView not found")
  )
)
"""

def build_export_schematic_script(
    lib: str,
    cell: str,
    view: str = "schematic",
    output_png: str = "schematic.png",
    width: int = 1920,
    height: int = 1080,
    bbox: str = "nil"
) -> str:
    bbox_arg = f"?bBox {bbox}" if bbox and bbox != "nil" else ""
    return f"""
let((win)
  win = geOpen(?lib "{lib}" ?cell "{cell}" ?view "{view}" ?mode "r")
  if(win then
    hiExportImage(?window win 
                  ?fileName "{output_png}" 
                  ?fileType "PNG" 
                  {bbox_arg}
                  ?width {width} 
                  ?height {height})
    hiCloseWindow(win)
    "{output_png}"
  else
    "ERROR: Could not open schematic"
  )
)
"""

def build_dc_operating_point_script(results_dir: str, instance: str) -> str:
    return f"""
let((results)
  openResults("{results_dir}")
  selectResult('dcOpInfo)
  list(
    list("instance" "{instance}")
    list("gm" pv("{instance}" "gm" ?result 'dcOpInfo))
    list("gds" pv("{instance}" "gds" ?result 'dcOpInfo))
    list("vth" pv("{instance}" "vth" ?result 'dcOpInfo))
    list("vdsat" pv("{instance}" "vdsat" ?result 'dcOpInfo))
    list("region" pv("{instance}" "region" ?result 'dcOpInfo))
    list("ids" pv("{instance}" "ids" ?result 'dcOpInfo))
    list("vgs" pv("{instance}" "vgs" ?result 'dcOpInfo))
    list("vds" pv("{instance}" "vds" ?result 'dcOpInfo))
  )
)
"""

def build_ocean_simulation_script(
    lib: str,
    cell: str,
    view: str = "schematic",
    extra_commands: str = ""
) -> str:
    return f"""
ocnWaveformTool('viva)
simulator('spectre)
design("{lib}" "{cell}" "{view}")
createNetlist()
{extra_commands.strip()}
run()
"""
