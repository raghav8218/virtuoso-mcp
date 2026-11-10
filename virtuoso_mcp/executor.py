import os
import subprocess
import logging
from abc import ABC, abstractmethod
from typing import Tuple, Optional
from .config import VirtuosoConfig
from .skill_helpers import wrap_skill

logger = logging.getLogger(__name__)

class VirtuosoExecutor(ABC):
    def __init__(self, config: VirtuosoConfig):
        self.config = config

    @abstractmethod
    def execute_skill(self, code: str, timeout: Optional[float] = None) -> str:
        pass

    @abstractmethod
    def run_command(self, cmd: str, timeout: Optional[float] = None) -> Tuple[int, str, str]:
        pass

    @abstractmethod
    def pull_file(self, remote_path: str, local_path: str) -> bool:
        pass


class LocalExecutor(VirtuosoExecutor):
    def execute_skill(self, code: str, timeout: Optional[float] = None) -> str:
        to = timeout or self.config.timeout
        work_dir = os.path.expanduser(self.config.remote_work_dir)
        os.makedirs(work_dir, exist_ok=True)
        
        script_file = os.path.join(work_dir, "_mcp_exec.il")
        out_file = os.path.join(work_dir, "_mcp_output.txt")
        
        if os.path.exists(out_file):
            try:
                os.remove(out_file)
            except OSError:
                pass
                
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(wrap_skill(code, out_file))
            
        self.run_command(f"virtuoso -nograph -replay {script_file}", timeout=to)
        
        if os.path.exists(out_file):
            with open(out_file, "r", encoding="utf-8", errors="replace") as f:
                return f.read().strip()
        return "ERROR: no output produced"

    def run_command(self, cmd: str, timeout: Optional[float] = None) -> Tuple[int, str, str]:
        to = timeout or self.config.timeout
        work_dir = os.path.expanduser(self.config.remote_work_dir)
        
        full_cmd = cmd
        if self.config.cshrc_path and os.path.exists(self.config.cshrc_path):
            full_cmd = f"source {self.config.cshrc_path} && {cmd}"
            
        proc = subprocess.run(
            full_cmd,
            shell=True,
            cwd=work_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=to
        )
        return proc.returncode, proc.stdout.decode("utf-8", errors="replace"), proc.stderr.decode("utf-8", errors="replace")

    def pull_file(self, remote_path: str, local_path: str) -> bool:
        import shutil
        src = os.path.abspath(os.path.expanduser(remote_path))
        dst = os.path.abspath(local_path)
        if src != dst and os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            return True
        return os.path.exists(dst)


class SSHExecutor(VirtuosoExecutor):
    def execute_skill(self, code: str, timeout: Optional[float] = None) -> str:
        to = timeout or self.config.timeout
        work_dir = self.config.remote_work_dir
        out_file = f"{work_dir}/_mcp_output.txt"
        script_file = f"{work_dir}/_mcp_exec.il"
        
        script = wrap_skill(code, out_file)
        
        csh_script = f"""
source {self.config.cshrc_path}
cd {work_dir}
rm -f {out_file}
cat << 'EOF' > {script_file}
{script}
EOF
virtuoso -nograph -replay {script_file} >& /dev/null
if ( -f {out_file} ) then
    cat {out_file}
else
    echo "ERROR: virtuoso produced no output"
endif
exit
"""
        _, stdout, _ = self._ssh(csh_script, to)
        return stdout.strip()

    def run_command(self, cmd: str, timeout: Optional[float] = None) -> Tuple[int, str, str]:
        to = timeout or self.config.timeout
        csh_cmd = f"source {self.config.cshrc_path}\ncd {self.config.remote_work_dir}\n{cmd}\nexit\n"
        return self._ssh(csh_cmd, to)

    def pull_file(self, remote_path: str, local_path: str) -> bool:
        os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
        user_host = f"{self.config.ssh_user}@{self.config.ssh_host}" if self.config.ssh_user else self.config.ssh_host
        
        # -O uses legacy scp protocol (more reliable on older lab clusters)
        scp_cmd = ["scp", "-O"]
        if self.config.ssh_key_path:
            scp_cmd += ["-i", self.config.ssh_key_path]
        if self.config.ssh_port != 22:
            scp_cmd += ["-P", str(self.config.ssh_port)]
        scp_cmd += [f"{user_host}:{remote_path}", local_path]
        
        try:
            res = subprocess.run(scp_cmd, capture_output=True, timeout=30)
            return res.returncode == 0
        except Exception:
            return False

    def _ssh(self, script: str, timeout: float) -> Tuple[int, str, str]:
        user_host = f"{self.config.ssh_user}@{self.config.ssh_host}" if self.config.ssh_user else self.config.ssh_host
        cmd = ["ssh", "-o", "BatchMode=yes"]
        if self.config.ssh_key_path:
            cmd += ["-i", self.config.ssh_key_path]
        if self.config.ssh_port != 22:
            cmd += ["-p", str(self.config.ssh_port)]
        cmd += [user_host, "csh"]
        
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            out, err = proc.communicate(input=script.encode("utf-8"), timeout=timeout)
            return proc.returncode, out.decode("utf-8", errors="replace"), err.decode("utf-8", errors="replace")
        except subprocess.TimeoutExpired:
            proc.kill()
            return -1, "", f"timed out after {timeout}s"


def get_executor(config: VirtuosoConfig) -> VirtuosoExecutor:
    if config.mode == "local":
        return LocalExecutor(config)
    return SSHExecutor(config)
