# Setup del Entorno Virtual (.venv)

Este proyecto utiliza un entorno virtual de Python para aislar dependencias.

## Requisitos previos

* Python 3 instalado
* `pip` disponible

---

## 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd <NOMBRE_DEL_PROYECTO>
```

---

## 2. Crear el entorno virtual

```bash
python -m venv .venv
```

---

## 3. Activar el entorno

### Windows (PowerShell)

```bash
.venv\Scripts\Activate.ps1
```

### Windows (CMD)

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

---

## 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## 5. Verificar instalación

```bash
pip list
```

---

## 6. Desactivar entorno

```bash
deactivate
```

---

## Notas

* El entorno `.venv` no se incluye en el repositorio.
* Si hay errores en Windows con PowerShell:

```bash
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```