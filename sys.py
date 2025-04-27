import sys

# Muestra la ruta del intérprete Python que se está usando
print("Python executable:", sys.executable)

# Instrucciones para instalar paquetes en ese intérprete
print("""
Para instalar paquetes en el intérprete Python que estás usando, abre una terminal y ejecuta:

\"\"\"
{ruta_python} -m pip install nombre_paquete
\"\"\"

Sustituye {ruta_python} por la ruta que se muestra arriba y nombre_paquete por el paquete que quieras instalar.

Ejemplo:
{ruta_python} -m pip install fastapi
""".format(ruta_python=sys.executable))
