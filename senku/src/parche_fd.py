"""Parche del bug de decodificacion UTF-8 en `up-fast-downward 0.5.2`.

El paquete `up-fast-downward 0.5.2` (la version instalada al hacer
`pip install up-fast-downward`) llama internamente a `bytes.decode()`
sin pasar `errors='replace'`. Cuando la salida estandar o de error de
Fast Downward contiene caracteres con tildes (frecuente en mensajes en
espanol), el decode lanza `UnicodeDecodeError` y la llamada al
planificador se rompe sin devolver el plan ni el estado.

Este modulo monkey-patchea `unified_planning.engines.pddl_planner.run_command`
para que use `errors='replace'`, neutralizando el bug sin afectar a la
correccion del resultado.

Uso:

    from senku.src.parche_fd import aplicar_parche
    aplicar_parche()
    # ... ahora ya se puede llamar a OneshotPlanner('fast-downward').solve(...)
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
    """Version de `run_command` que decodifica la salida con
    `errors='replace'`, evitando el UnicodeDecodeError del paquete
    original."""
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
            # FIX: decodificacion tolerante a bytes no validos en UTF-8.
            proc_out, proc_err = [
                [x.decode(errors="replace")] for x in out_err_bytes
            ]
        except subprocess.TimeoutExpired:
            from unified_planning.engines.pddl_planner import terminate_process
            terminate_process(engine._process)
            timeout_occurred = True
        retval = engine._process.returncode if engine._process else 0
        return timeout_occurred, (proc_out, proc_err), retval

    # Si se pasa un output_stream, delegamos en la implementacion original
    # tras recargarla (caso poco habitual en este trabajo).
    import unified_planning.engines.pddl_planner as pddl_planner
    return pddl_planner.run_command.__wrapped__(  # type: ignore[attr-defined]
        engine, cmd, output_stream=output_stream, timeout=timeout
    )
