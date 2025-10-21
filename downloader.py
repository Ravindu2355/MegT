import subprocess, shutil, os, uuid, json
from pathlib import Path
from config import DOWNLOADS_DIR, MEGA_CLI

def _run_cmd(cmd, cwd=None, timeout=None):
    try:
        p = subprocess.run(cmd, shell=False, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, timeout=timeout)
        return p.stdout.decode(errors="ignore"), p.stderr.decode(errors="ignore")
    except subprocess.CalledProcessError as e:
        return None, e.stderr.decode(errors="ignore")
    except Exception as e:
        return None, str(e)

def download_mega_link(mega_link):
    """
    Downloads a MEGA link (file or folder) into a unique folder. Returns list of files downloaded:
    [ { "local_path": "/path/to/file", "size": 12345, "name": "xxx" }, ... ]
    Requires MEGA_CLI to be installed: "megadl" (megatools) or "mega-get" (megacmd).
    """
    dest_dir = Path(DOWNLOADS_DIR) / str(uuid.uuid4())
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Try megadl (megatools) first if configured
    if MEGA_CLI == "megadl":
        cmd = ["megadl", "--path", str(dest_dir), "--no-progress", mega_link]
        out, err = _run_cmd(cmd)
        if out is None:
            # fallback to mega-get if installed
            cmd2 = ["mega-get", mega_link, str(dest_dir)]
            out2, err2 = _run_cmd(cmd2)
            if out2 is None:
                raise RuntimeError(f"Both megadl and mega-get failed. megadl err: {err}\nmega-get err: {err2}")
    else:
        # configured for mega-get
        cmd = ["mega-get", mega_link, str(dest_dir)]
        out, err = _run_cmd(cmd)
        if out is None:
            # fallback to megadl
            cmd2 = ["megadl", "--path", str(dest_dir), "--no-progress", mega_link]
            out2, err2 = _run_cmd(cmd2)
            if out2 is None:
                raise RuntimeError(f"Both mega-get and megadl failed. mega-get err: {err}\nmegadl err: {err2}")

    # Walk downloaded folder and list files
    files = []
    for p in dest_dir.rglob("*"):
        if p.is_file():
            files.append({
                "local_path": str(p),
                "size": p.stat().st_size,
                "name": p.name
            })
    # Sort to get deterministic order (optional)
    files.sort(key=lambda x: x["name"])
    return files
