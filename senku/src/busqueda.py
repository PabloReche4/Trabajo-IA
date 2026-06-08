"""Algoritmos de busqueda sobre el espacio de estados del Senku.

  - busqueda_primero_anchura: BFS (parte comun del trabajo).
  - busqueda_primero_profundidad: DFS con limite, como referencia.
  - beam_search: ampliacion de junio.
  - beam_search_con_reinicios: variante con desempate aleatorio.
  - beam_search_iterativo: anchura creciente.

Todos devuelven un objeto Resultado con el plan (si existe) y las
estadisticas basicas (nodos, tiempo, parametros, min_piezas...).
"""

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Set
import random
import time
from collections import deque

from .estado import Estado, Movimiento, ProblemaSenku, reconstruye_camino


@dataclass
class Resultado:
    """Resultado homogeneo de cualquiera de las busquedas.

    - exito: True si se alcanzo la meta.
    - movimientos / estados: plan encontrado (vacio si no hubo exito).
    - nodos_expandidos, tiempo_segundos: estadisticas.
    - parametros: metadatos del algoritmo (beta, intentos, etc.).
    - min_piezas_alcanzadas: el menor numero de piezas que aparecio en
      algun estado explorado. Sirve para diagnosticar cuanto se quedo
      cerca cuando no hay exito.
    """

    exito: bool
    movimientos: List[Movimiento] = field(default_factory=list)
    estados: List[Estado] = field(default_factory=list)
    nodos_expandidos: int = 0
    tiempo_segundos: float = 0.0
    parametros: dict = field(default_factory=dict)
    min_piezas_alcanzadas: Optional[int] = None

    def __str__(self) -> str:
        cabecera = "Solucion encontrada" if self.exito else "Sin solucion"
        extra = ""
        if not self.exito and self.min_piezas_alcanzadas is not None:
            extra = f" | min_piezas={self.min_piezas_alcanzadas}"
        return (
            f"{cabecera} | movimientos={len(self.movimientos)} "
            f"| nodos={self.nodos_expandidos} | tiempo={self.tiempo_segundos:.3f}s "
            f"| params={self.parametros}{extra}"
        )


def busqueda_primero_anchura(
    problema: ProblemaSenku, limite_nodos: Optional[int] = None
) -> Resultado:
    """BFS clasica: encuentra el plan con menos movimientos posible.

    limite_nodos acota la exploracion: el espacio de estados del Senku
    es exponencial y BFS sin cota se vuelve inviable rapidamente."""
    inicio = time.perf_counter()
    if problema.es_meta(problema.inicial):
        return Resultado(
            exito=True,
            estados=[problema.inicial],
            tiempo_segundos=time.perf_counter() - inicio,
            parametros={"algoritmo": "BFS"},
        )

    visitados: Set[Estado] = {problema.inicial}
    padres = {problema.inicial: None}
    cola = deque([problema.inicial])
    expandidos = 0

    while cola:
        estado = cola.popleft()
        expandidos += 1
        if limite_nodos is not None and expandidos > limite_nodos:
            break
        for movimiento, sucesor in problema.sucesores(estado):
            if sucesor in visitados:
                continue
            visitados.add(sucesor)
            padres[sucesor] = (movimiento, estado)
            if problema.es_meta(sucesor):
                estados, movimientos = reconstruye_camino(padres, sucesor)
                return Resultado(
                    exito=True,
                    estados=estados,
                    movimientos=movimientos,
                    nodos_expandidos=expandidos,
                    tiempo_segundos=time.perf_counter() - inicio,
                    parametros={"algoritmo": "BFS"},
                )
            cola.append(sucesor)
    return Resultado(
        exito=False,
        nodos_expandidos=expandidos,
        tiempo_segundos=time.perf_counter() - inicio,
        parametros={"algoritmo": "BFS", "limite_nodos": limite_nodos},
    )


def busqueda_primero_profundidad(
    problema: ProblemaSenku, limite_profundidad: Optional[int] = None
) -> Resultado:
    """DFS iterativa con limite de profundidad.

    No es la herramienta principal del trabajo; se incluye como
    referencia para comparar contra el beam search."""
    inicio = time.perf_counter()
    pila = [(problema.inicial, [], [problema.inicial])]
    expandidos = 0

    while pila:
        estado, movimientos, camino = pila.pop()
        expandidos += 1
        if problema.es_meta(estado):
            return Resultado(
                exito=True,
                estados=camino,
                movimientos=movimientos,
                nodos_expandidos=expandidos,
                tiempo_segundos=time.perf_counter() - inicio,
                parametros={"algoritmo": "DFS"},
            )
        if limite_profundidad is not None and len(movimientos) >= limite_profundidad:
            continue
        for movimiento, sucesor in problema.sucesores(estado):
            if sucesor in camino:
                continue
            pila.append((sucesor, movimientos + [movimiento], camino + [sucesor]))
    return Resultado(
        exito=False,
        nodos_expandidos=expandidos,
        tiempo_segundos=time.perf_counter() - inicio,
        parametros={"algoritmo": "DFS", "limite_profundidad": limite_profundidad},
    )


def beam_search(
    problema: ProblemaSenku,
    heuristica: Callable[[Estado], float],
    beta: int = 10,
    iteraciones_maximas: Optional[int] = None,
    usar_visitados: bool = True,
    semilla: Optional[int] = None,
) -> Resultado:
    """Beam Search siguiendo el pseudocodigo del enunciado.

    Esquema:
      1. Frontera inicial = {estado_0}.
      2. Por cada estado de la frontera, generamos sus sucesores.
      3. Si alguno es meta, devolvemos el plan.
      4. Si no, ordenamos los sucesores por la heuristica y nos
         quedamos con los `beta` mejores como nueva frontera.

    usar_visitados: si esta activo, mantenemos un set global para no
    re-explorar estados ya vistos. Apagarlo permite revisitas (a veces
    util cuando la heuristica empuja la busqueda a callejones).
    semilla: alimenta el generador aleatorio que desempata estados con
    la misma heuristica, util para reproducir y para diversificar.
    """
    inicio = time.perf_counter()
    rng = random.Random(semilla)
    if problema.es_meta(problema.inicial):
        return Resultado(
            exito=True,
            estados=[problema.inicial],
            tiempo_segundos=time.perf_counter() - inicio,
            parametros={"algoritmo": "BeamSearch", "beta": beta},
        )

    padres = {problema.inicial: None}
    visitados: Set[Estado] = {problema.inicial} if usar_visitados else set()
    frontera: List[Estado] = [problema.inicial]
    expandidos = 0
    iteraciones = 0
    # Tracking del estado mas cercano a la meta encontrado (con menos piezas).
    min_piezas = len(problema.inicial)

    while frontera:
        iteraciones += 1
        if iteraciones_maximas is not None and iteraciones > iteraciones_maximas:
            break
        candidatos = []
        for estado in frontera:
            expandidos += 1
            for movimiento, sucesor in problema.sucesores(estado):
                if usar_visitados and sucesor in visitados:
                    continue
                # Solo registramos padre la primera vez que vemos el estado
                if sucesor not in padres:
                    padres[sucesor] = (movimiento, estado)
                if len(sucesor) < min_piezas:
                    min_piezas = len(sucesor)
                if problema.es_meta(sucesor):
                    estados, movimientos = reconstruye_camino(padres, sucesor)
                    return Resultado(
                        exito=True,
                        estados=estados,
                        movimientos=movimientos,
                        nodos_expandidos=expandidos,
                        tiempo_segundos=time.perf_counter() - inicio,
                        parametros={
                            "algoritmo": "BeamSearch",
                            "beta": beta,
                            "iteraciones": iteraciones,
                            "usar_visitados": usar_visitados,
                        },
                        min_piezas_alcanzadas=len(sucesor),
                    )
                if usar_visitados:
                    visitados.add(sucesor)
                candidatos.append((heuristica(sucesor), sucesor))
        candidatos = [c for c in candidatos if c[0] != float("inf")]
        # Anadimos un valor aleatorio como segundo criterio para que
        # estados con la misma heuristica no se ordenen siempre igual.
        candidatos.sort(key=lambda x: (x[0], rng.random()))
        frontera = [estado for _, estado in candidatos[:beta]]

    return Resultado(
        exito=False,
        nodos_expandidos=expandidos,
        tiempo_segundos=time.perf_counter() - inicio,
        min_piezas_alcanzadas=min_piezas,
        parametros={
            "algoritmo": "BeamSearch",
            "beta": beta,
            "iteraciones": iteraciones,
            "usar_visitados": usar_visitados,
        },
    )


def beam_search_con_reinicios(
    problema: ProblemaSenku,
    heuristica: Callable[[Estado], float],
    beta: int = 10,
    intentos: int = 5,
    iteraciones_maximas: Optional[int] = None,
    usar_visitados: bool = True,
) -> Resultado:
    """Repite beam_search con distintas semillas y devuelve el primer
    intento exitoso (o el ultimo fallido si ninguno acierta).

    Beam search es incompleto: con un desempate determinista puede
    quedarse siempre en el mismo callejon. Variando la semilla cada
    intento explora distintas ramas y la probabilidad de exito sube
    de forma apreciable en problemas con soluciones tan escasas como
    el Senku."""
    mejor_fallo = None
    inicio_total = time.perf_counter()
    nodos_totales = 0
    min_piezas_globales = len(problema.inicial)
    for intento in range(intentos):
        r = beam_search(
            problema=problema,
            heuristica=heuristica,
            beta=beta,
            iteraciones_maximas=iteraciones_maximas,
            usar_visitados=usar_visitados,
            semilla=intento,
        )
        nodos_totales += r.nodos_expandidos
        if r.min_piezas_alcanzadas is not None:
            min_piezas_globales = min(min_piezas_globales, r.min_piezas_alcanzadas)
        if r.exito:
            r.tiempo_segundos = time.perf_counter() - inicio_total
            r.nodos_expandidos = nodos_totales
            r.parametros["intento_exitoso"] = intento
            r.parametros["intentos_totales"] = intento + 1
            return r
        mejor_fallo = r
    if mejor_fallo is not None:
        mejor_fallo.tiempo_segundos = time.perf_counter() - inicio_total
        mejor_fallo.nodos_expandidos = nodos_totales
        mejor_fallo.min_piezas_alcanzadas = min_piezas_globales
        mejor_fallo.parametros["intentos_totales"] = intentos
    return mejor_fallo  # type: ignore[return-value]


def beam_search_iterativo(
    problema: ProblemaSenku,
    heuristica: Callable[[Estado], float],
    betas: Optional[List[int]] = None,
    intentos_por_beta: int = 3,
    iteraciones_maximas: Optional[int] = None,
    usar_visitados: bool = True,
) -> Resultado:
    """Beam search con anchura creciente.

    Si una anchura no encuentra plan, se reintenta con la siguiente.
    En la literatura se conoce como iterative widening beam search.
    Empieza con el beta mas pequeno (rapido) y solo gasta mas
    presupuesto si hace falta: instancias faciles salen baratas y las
    dificiles siguen cubiertas.

    betas: lista creciente de anchuras (por defecto [100, 300, 800, 1500]).
    intentos_por_beta: reinicios estocasticos por cada anchura.
    """
    if betas is None:
        betas = [100, 300, 800, 1500]
    inicio = time.perf_counter()
    nodos_totales = 0
    min_piezas_globales = len(problema.inicial)
    ultimo = None
    for beta in betas:
        r = beam_search_con_reinicios(
            problema=problema,
            heuristica=heuristica,
            beta=beta,
            intentos=intentos_por_beta,
            iteraciones_maximas=iteraciones_maximas,
            usar_visitados=usar_visitados,
        )
        nodos_totales += r.nodos_expandidos
        if r.min_piezas_alcanzadas is not None:
            min_piezas_globales = min(min_piezas_globales, r.min_piezas_alcanzadas)
        if r.exito:
            r.tiempo_segundos = time.perf_counter() - inicio
            r.nodos_expandidos = nodos_totales
            r.parametros["algoritmo"] = "BeamSearchIterativo"
            r.parametros["beta_exitoso"] = beta
            r.parametros["betas_probados"] = betas[: betas.index(beta) + 1]
            return r
        ultimo = r
    if ultimo is not None:
        ultimo.tiempo_segundos = time.perf_counter() - inicio
        ultimo.nodos_expandidos = nodos_totales
        ultimo.min_piezas_alcanzadas = min_piezas_globales
        ultimo.parametros["algoritmo"] = "BeamSearchIterativo"
        ultimo.parametros["betas_probados"] = betas
    return ultimo  # type: ignore[return-value]
