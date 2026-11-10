import os
import json
from typing import Optional, Literal
from pydantic import BaseModel

class VirtuosoConfig(BaseModel):
    mode: Literal["ssh", "local"] = "ssh"
    
    # ssh settings
    ssh_host: Optional[str] = "eda-uni"
    ssh_port: int = 22
    ssh_user: Optional[str] = "ISDL_UG_107"
    ssh_key_path: Optional[str] = None
    
    # cadence paths
    remote_work_dir: str = "/home/ISDL_UG_107/work"
    cshrc_path: str = "/cad/cshrc"
    virtuoso_command: str = "virtuoso -nograph -replay"
    default_library: str = "EE301_2026"
    timeout: float = 60.0

    @classmethod
    def load(cls, path: Optional[str] = None) -> "VirtuosoConfig":
        search_paths = [
            path,
            "config.json",
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json"),
        ]
        for p in search_paths:
            if p and os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    return cls(**json.load(f))
        return cls()
