@echo off
SETLOCAL

echo ------------------------------
echo 🔹 Configurando proyecto...
echo ------------------------------

:: Crear virtual environment si no existe
IF NOT EXIST venv (
    echo Creando entorno virtual...
    python -m venv venv
) ELSE (
    echo Entorno virtual ya existe.
)

:: Activar entorno virtual
echo Activando entorno virtual...
call venv\Scripts\activate

:: Actualizar pip
echo Actualizando pip...
python -m pip install --upgrade pip

:: Instalar dependencias
IF EXIST requirements.txt (
    echo Instalando dependencias desde requirements.txt...
    pip install -r requirements.txt
) ELSE (
    echo No se encontro requirements.txt, omitiendo instalacion de dependencias.
)

echo ------------------------------
echo ✅ Proyecto listo!
echo Activa el venv con: call venv\Scripts\activate
echo Ejecuta la app con: python app.py
echo ------------------------------

pause
ENDLOCAL