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

## Cómo sincronizar en otra computadora

Cada vez que alguien clone el proyecto, solo debe hacer esto:

```bash
git clone https://github.com/TU_USUARIO/pedidos-huevo-streamlit.git
cd pedidos-huevo-streamlit
uv sync
```

Y para abrir la app:

```bash
uv run streamlit run app.py
```

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

## Reglas del sistema

* no se permiten valores negativos
* el total por colaborador no puede ser mayor a 3
* solo se incluyen en el Excel final los colaboradores con pedido mayor a 0
* el correo del colaborador no va al Excel
* el correo del colaborador solo sirve para copia automática
* las copias automáticas se agregan solo para colaboradores que sí hicieron pedido y tienen correo

---

## Archivos importantes

### `data/catalogos/colaboradores.json`

Ejemplo:

```json
[
  {
    "id": 1,
    "nombre": "Claudia Cime",
    "area": "Soporte SAP",
    "correo": "claudia@empresa.com",
    "activo": true
  }
]
```

### `data/catalogos/destinatarios.json`

Ejemplo:

```json
[
  {
    "id": 1,
    "nombre": "Compras corporativo",
    "correo": "compras@empresa.com",
    "activo": true
  }
]
```

### `data/catalogos/config_envio.json`

Ejemplo:

```json
{
  "destinatario_principal_id": 1,
  "copias_destinatarios_ids": [2],
  "asunto_base": "Pedido semanal de huevo",
  "mensaje_base": "Buen día,\n\nComparto el archivo semanal de pedidos de huevo.\n"
}
```

---

## Archivos generados

La app genera archivos Excel en:

```text
data/output/
```

---

## `.gitignore` recomendado

```gitignore
.venv/
__pycache__/
*.pyc
.env
data/output/*.xlsx
data/output/*.csv
data/output/*.json
!.gitkeep
```

---

## Comandos principales

### Clonar

```bash
git clone https://github.com/TU_USUARIO/pedidos-huevo-streamlit.git
cd pedidos-huevo-streamlit
```

### Sincronizar

```bash
uv sync
```

### Ejecutar

```bash
uv run streamlit run app.py
```

---

## Problemas comunes

### No carga SMTP

Revisar que exista el archivo `.env` en la raíz.

### No genera Excel

Revisar que exista:

```text
data/templates/PEDIDOS_CORPORATIVO.xlsx
```

### No envía correo

Revisar:

* SMTP
* usuario y contraseña
* App Password si usas Gmail
* destinatario principal configurado
* archivo Excel generado

---

## Versión actual

**v1**

```
```
