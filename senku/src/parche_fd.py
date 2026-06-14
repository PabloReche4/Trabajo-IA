"""Parche para el bug de decodificacion UTF-8 de up-fast-downward 0.5.2.

up-fast-downward 0.5.2 (la version que sale por defecto al hacer
`pip install up-fast-downward`) llama internamente a `bytes.decode()`
sin `errors='replace'`. Cuando la salida de Fast Downward incluye
caracteres con tildes (en Windows pasa con bastante frecuencia), el
decode lanza UnicodeDecodeError y la llamada se queda colgada sin
devolver plan ni estado.

Aqui monkey-parcheamos `unified_planning.engines.pddl_planner.run_command`
para que decodifique con `errors='replace'`. Es la solucion minima que
arregla el bug sin tocar nada mas.

Uso:

    from senku.src.parche_fd import aplicar_parche
    aplicar_parche()
    # OneshotPlanner('fast-downward') ya funciona.
"""

from typing import IO, List, Optional, Tuple, Union
import subprocess
import sys

_PARCHE_APLICADO = False


def aplicar_parche() -> None:
    """Aplica el parche una sola vez (idempotente)."""
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
    """run_command que decodifica la salida con errors='replace'."""
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
            # Aqui esta el fix: decode tolerante a bytes no validos.
            proc_out, proc_err = [
                [x.decode(errors="replace")] for x in out_err_bytes
            ]
        except subprocess.TimeoutExpired:
            from unified_planning.engines.pddl_planner import terminate_process
            terminate_process(engine._process)
            timeout_occurred = True
        retval = engine._process.returncode if engine._process else 0
        return timeout_occurred, (proc_out, proc_err), retval

    # Si llega un output_stream, delegamos en la implementacion original
    # (es un caso que no usamos en el trabajo).
    import unified_planning.engines.pddl_planner as pddl_planner
    return pddl_planner.run_command.__wrapped__(  # type: ignore[attr-defined]
        engine, cmd, output_stream=output_stream, timeout=timeout
    )
