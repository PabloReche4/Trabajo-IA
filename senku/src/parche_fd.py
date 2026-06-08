"""Parche del UnicodeDecodeError de up-fast-downward 0.5.2 en Windows.

up-fast-downward 0.5.2 decodifica la salida de Fast Downward sin
errors='replace', lo que lanza UnicodeDecodeError cuando aparecen
caracteres con tilde. Aqui parcheamos run_command para que use
errors='replace'.
"""

from typing import IO, List, Optional, Tuple, Union
import subprocess
import sys

_PARCHE_APLICADO = False


def aplicar_parche() -> None:
    global _PARCHE_APLICADO
    if _PARCHE_APLICADO:
        return
    import unified_planning.engines.pddl_planner as pddl_planner
    pddl_planner.run_command = _run_command_tolerante
    _PARCHE_APLICADO = True


def _run_command_tolerante(
    engine,
    cmd: List[str],
    output_stream: Optional[Union[Tuple[IO[str], IO[str]], IO[str]]] = None,
    timeout: Optional[float] = None,
) -> Tuple[bool, Tuple[List[str], List[str]], int]:
    if output_stream is None:
        kwargs = (
            {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}  # type: ignore[attr-defined]
            if sys.platform == "win32"
            else {"start_new_session": True}
        )
        engine._process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs
        )
        timeout_occurred = False
        proc_out: List[str] = []
        proc_err: List[str] = []
        try:
            out_err_bytes = engine._process.communicate(timeout=timeout)
            proc_out, proc_err = [
                [x.decode(errors="replace")] for x in out_err_bytes
            ]
        except subprocess.TimeoutExpired:
            from unified_planning.engines.pddl_planner import terminate_process
            terminate_process(engine._process)
            timeout_occurred = True
        retval = engine._process.returncode if engine._process else 0
        return timeout_occurred, (proc_out, proc_err), retval

    import unified_planning.engines.pddl_planner as pddl_planner
    return pddl_planner.run_command.__wrapped__(  # type: ignore[attr-defined]
        engine, cmd, output_stream=output_stream, timeout=timeout
    )
