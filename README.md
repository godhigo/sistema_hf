# Sistema de Gestión para Podología 🦶💼

[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-2.3-green)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/mysql-8.0-orange)](https://www.mysql.com/)

Sistema web desarrollado en **Flask** para la gestión de un negocio de podología. Permite administrar citas, clientes, empleados, servicios, ventas y visualizar métricas en un dashboard interactivo.

---

## Funcionalidades

- Autenticación de usuarios (login/signup) con contraseña segura.  
- Registro y gestión de clientes y empleados.  
- Registro de citas con validación de conflictos de horarios.  
- Gestión de ventas y cálculo de ganancias.  
- Dashboard con métricas y gráficas:
  - Citas del día
  - Clientes registrados
  - Empleados activos
  - Ventas de la semana
  - Gráfica de ventas últimos 7 días
  - Gráfica de servicios más vendidos  
- Posibilidad de subir fotos de empleados.  
- Manejo de errores personalizados (404 y 500).

---

## Tecnologías usadas

- **Backend:** Python, Flask  
- **Base de datos:** MySQL  
- **Frontend:** HTML, CSS, JavaScript, FontAwesome  
- **Seguridad:** Flask-Login, werkzeug.security  
- **Gráficas:** Chart.js  
- **Entorno virtual:** venv  
- **Gestión de dependencias:** pip (`requirements.txt`)  

---

## Instalación

1. Clona el repositorio:

```bash
git clone https://github.com/godhigo/sistema_hf.git
cd sistema_hf
```

2. Crea tu entorno virtual:

```bash
python -m venv venv
```

3. Activa el entorno virtual:

Windows: 
```bash
venv\Scripts\activate
```

Mac/Linux
```bash
source venv/bin/activate
```

4. Instala las dependencias:

```bash
pip install -r requirements.txt
```

5. Crea un archivo .env en la raíz del proyecto con tus variables:

```ini
FLASK_SECRET_KEY=tu_clave_secreta
ADMIN_REGISTER_PASSWORD=tu_clave_maestra
DB_HOST=host_de_tu_db
DB_USER=usuario_de_tu_db
DB_PASSWORD=contraseña_de_tu_db
DB_NAME=nombre_de_tu_db
```

6. Corre la aplicación:

```bash
python app.py
```

Estructura del Proyecto:

```php
sistema_hf/
│
├── app.py
├── db.py
├── requirements.txt
├── setup.bat
├── .gitignore
├── README.md
├── database/
│   └── schema.sql
├── static/
│   ├── citas.css
│   ├── clientes.css
│   ├── empleados.css
│   ├── index.css
│   ├── mensaje.css
│   ├── sidebar.css
│   ├── signup.css
│   └── ventas.css
├── templates/
│   ├── citas.html
│   ├── clientes.html
│   ├── editar_cita.html
│   ├── empleados.html
│   ├── index.html
│   ├── login.html
│   ├── mensaje.html
│   ├── sidebar.html
│   ├── signup.html
│   └── ventas.html
```

NOTAS IMPORTANTES:

-No subir .env ni la carpeta venv/ al repositorio.

-Configura la base de datos correctamente en .env.

-Para producción, se recomienda usar un servidor seguro y SSL.

AUTOR:

Diego Navarro Sánchez - Proyecto sistema de gestión