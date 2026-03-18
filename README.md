[README.md](sandbox:/mnt/data/README.md)

# Pedidos de huevo semanal · v1

Aplicación interna en **Streamlit** para capturar pedidos semanales de huevo, generar un archivo **Excel** a partir de un template y enviarlo por correo automáticamente.

---

## Inicio rápido

### 1. Clonar el proyecto

```bash
git clone https://github.com/TU_USUARIO/pedidos-huevo-streamlit.git
cd pedidos-huevo-streamlit
````

### 2. Sincronizar el entorno con uv

```bash
uv sync
```

Con eso queda listo el entorno local del proyecto con las dependencias y versiones definidas aquí.

### 3. Ejecutar la app

```bash
uv run streamlit run app.py
```

---

## Idea principal del proyecto

La app automatiza este flujo:

1. capturar pedidos por colaborador
2. generar el Excel final usando el mismo template semanal
3. enviar un solo correo con el archivo adjunto

---

## Requisitos

* Python 3.12
* uv instalado

---

## Configuración adicional necesaria

Antes de usar la app por primera vez, revisa estos puntos.

### 1. Crear el archivo `.env`

Debes crear un archivo llamado `.env` en la raíz del proyecto.

Ejemplo:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_correo@empresa.com
SMTP_PASSWORD=TU_APP_PASSWORD
SMTP_USE_TLS=true
MAIL_FROM=tu_correo@empresa.com
MAIL_CC=
MAIL_BCC=
```

Este archivo define la cuenta que enviará el correo.

---

### 2. Colocar el template de Excel

Debes poner el template aquí:

```text
data/templates/PEDIDOS_CORPORATIVO.xlsx
```

La app usa ese archivo como base para generar el Excel final semanal.

---

### 3. Revisar archivos de catálogo

Revisa o edita estos archivos:

```text
data/catalogos/colaboradores.json
data/catalogos/destinatarios.json
data/catalogos/config_envio.json
```

---

---

## Estructura del proyecto

```text
pedidos_huevo_streamlit/
├─ app.py
├─ pyproject.toml
├─ uv.lock
├─ .env.example
├─ .gitignore
├─ README.md
├─ scripts/
│  └─ bootstrap_catalogs.py
├─ data/
│  ├─ catalogos/
│  │  ├─ colaboradores.json
│  │  ├─ destinatarios.json
│  │  └─ config_envio.json
│  ├─ templates/
│  │  └─ PEDIDOS_CORPORATIVO.xlsx
│  └─ output/
│     └─ .gitkeep
└─ src/
   └─ pedidos_huevo/
      ├─ __init__.py
      ├─ config.py
      ├─ storage.py
      └─ emailer.py
```

---

## Uso general

### Pestaña Captura

Aquí se hace la operación semanal:

* seleccionar colaborador
* capturar cantidades
* guardar pedido
* avanzar al siguiente
* generar el Excel final
* enviar el correo

### Pestaña Configuración

Aquí se deja listo el sistema:

* colaboradores
* correos de colaboradores
* destinatarios
* destinatario principal
* copias fijas
* asunto base
* mensaje base

---


## Versión actual

**v1**

```
```
