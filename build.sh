#!/usr/bin/env bash
# exit on error
set -o errexit

# Instalamos los requerimientos buscando el archivo dentro de la carpeta backend
pip install -r backend/requirements.txt

# Ejecutamos los comandos de Django apuntando al manage.py que está en backend
python backend/manage.py collectstatic --no-input
python backend/manage.py migrate