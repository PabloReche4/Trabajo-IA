# Memoria del trabajo — Cómo compilarla y verla

Esta carpeta contiene la memoria del trabajo en formato IEEE,
exactamente con la plantilla del profesor.

## Ficheros

| Fichero            | Qué es                                                    |
|--------------------|-----------------------------------------------------------|
| `memoria.tex`      | Fuente LaTeX. Es lo que hay que compilar para producir el PDF. |
| `memoria.md`       | Versión Markdown del mismo contenido (para leer / revisar sin compilar). |
| `presentacion.md`  | Guion de los 10 minutos de defensa.                       |
| `IEEEtran.cls`     | Clase LaTeX de IEEE (la misma del profesor).              |
| `ejemplo.jpg`      | Imagen de ejemplo de la plantilla original.               |

## Cómo abrir el `.tex` y obtener el PDF

### Opción A (RECOMENDADA): Overleaf — sin instalar nada

[Overleaf](https://www.overleaf.com) es un editor LaTeX online y gratuito.
Es lo más rápido para esta entrega.

1. Crear cuenta gratuita en <https://www.overleaf.com>.
2. *New Project* → *Upload Project*.
3. Subir un zip con TODA la carpeta `senku/memoria/` (al menos
   `memoria.tex`, `IEEEtran.cls` y `ejemplo.jpg`).
4. En el panel superior izquierdo, elegir `memoria.tex` como
   *Main document*.
5. Pulsar el botón verde **Recompile** → Overleaf muestra el PDF
   directamente en pantalla.
6. Botón *Download PDF* para tener el fichero final que se entrega.

### Opción B: Instalar LaTeX en Windows

1. Descargar e instalar [MiKTeX](https://miktex.org/download) (el
   instalador "Basic MiKTeX 64-bit"). Aceptar que descargue paquetes
   bajo demanda.
2. Descargar [TeXstudio](https://www.texstudio.org/) como editor
   gráfico (mucho más cómodo que la consola).
3. Abrir `senku/memoria/memoria.tex` con TeXstudio.
4. Pulsar F5 (o el botón *Build & View*). MiKTeX descargará los
   paquetes que falten la primera vez (`pseudo`, `booktabs`, etc.).
5. El PDF aparece en el visor integrado de TeXstudio. Queda
   disponible como `memoria.pdf` en la misma carpeta.

### Opción C: VSCode + LaTeX Workshop

Si ya usas VSCode:

1. Instalar MiKTeX o TeX Live (igual que la opción B).
2. En VSCode, instalar la extensión **LaTeX Workshop**.
3. Abrir la carpeta del proyecto, navegar a `senku/memoria/memoria.tex`
   y pulsar el icono de "build" (la flecha verde arriba a la derecha).
4. El PDF aparece en una pestaña lateral.

### Opción D: Compilación desde la consola (avanzado)

Una vez instalado MiKTeX/TeX Live:

```powershell
cd "c:\Users\betis\Desktop\trabajo IA\Trabajo-IA\senku\memoria"
pdflatex memoria.tex
pdflatex memoria.tex   # segunda pasada para fijar referencias
```

Se genera `memoria.pdf` en la misma carpeta. Para abrirlo:

```powershell
start memoria.pdf
```

## Editores recomendados para tocar el `.tex`

`memoria.tex` es texto plano: se puede editar con cualquier editor
(VSCode, Notepad++, TeXstudio, etc.). El PDF sólo se genera al
compilar.

## Paquetes LaTeX que necesita la plantilla

- `IEEEtran` (proporcionado en esta carpeta: `IEEEtran.cls`).
- `amsmath`, `graphicx`, `inputenc`, `fontenc` (estándar).
- `pseudo` (para el pseudocódigo).
- `booktabs` (para tablas).
- `cite` (para las referencias).

Tanto Overleaf como MiKTeX los instalan automáticamente.
