"""Execute clean notebook kernels using this exact virtual environment's Python."""

import json
import os
import sys
import tempfile
from pathlib import Path

import nbformat
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager
from nbclient import NotebookClient


def execute_notebooks() -> None:
    """Clear outputs, launch isolated kernels, and save only successful executions."""
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="quantiva-kernel-") as kernel_dir:
        folder = Path(kernel_dir) / "quantiva"
        folder.mkdir()
        (folder / "kernel.json").write_text(
            json.dumps(
                {
                    "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
                    "display_name": "Quantiva isolated kernel",
                    "language": "python",
                    "env": {"QUANTIVA_KERNEL_EXECUTABLE": sys.executable, "MPLBACKEND": "Agg"},
                }
            ),
            encoding="utf-8",
        )
        for path in sorted((root / "notebooks").glob("0[12]_*.ipynb")):
            notebook = nbformat.read(path, as_version=4)
            for cell in notebook.cells:
                if cell.cell_type == "code":
                    cell.outputs = []
                    cell.execution_count = None
            manager = KernelManager(
                kernel_name="quantiva",
                kernel_spec_manager=KernelSpecManager(kernel_dirs=[kernel_dir]),
            )
            try:
                NotebookClient(
                    notebook, km=manager, timeout=600, resources={"metadata": {"path": str(root)}}
                ).execute()
                nbformat.validate(notebook)
                nbformat.write(notebook, path)
            finally:
                if manager.has_kernel:
                    manager.shutdown_kernel(now=True)
            print(f"Executed successfully: {path.name}")


if __name__ == "__main__":
    # Windows asyncio compatibility is provided by the notebook client's kernel stack.
    os.environ.setdefault("MPLBACKEND", "Agg")
    execute_notebooks()
