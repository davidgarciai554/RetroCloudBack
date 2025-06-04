import sqlite3
import requests
import time
import re
from math import ceil
from requests.exceptions import HTTPError, RequestException

MAX_RESULTS = 200000
PAGE_SIZE   = 40
API_KEY     = "0085cd9d23e74fc3b1bc723f749f7f4a"
SLEEP_API   = 0.3
MAX_RETRIES = 200
RETRY_DELAY = 5

# Consolas a omitir por nombre (case-insensitive, exacto)
PLATAFORMAS_OMITIDAS = {"ios", "pc", "macos", "linux", "android", "web"}

def agregar_columna_si_no_existe(conn, tabla, columna, tipo):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({tabla})")
    columnas = [row[1] for row in cur.fetchall()]
    if columna not in columnas:
        cur.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}")
        conn.commit()

def crear_base_de_datos(conn):
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS EMPRESAS (
      ID INTEGER PRIMARY KEY AUTOINCREMENT,
      NOMBRE TEXT UNIQUE
    );
    CREATE TABLE IF NOT EXISTS CONSOLAS (
      ID INTEGER PRIMARY KEY,
      NOMBRE TEXT,
      EMPRESA_ID INTEGER,
      NUM_JUEGOS_API INTEGER,
      FOREIGN KEY (EMPRESA_ID) REFERENCES EMPRESAS(ID)
    );
    CREATE TABLE IF NOT EXISTS JUEGOS (
      ID INTEGER PRIMARY KEY,
      NOMBRE TEXT,
      FECHA_LANZAMIENTO TEXT,
      DESCRIPCION TEXT,
      PUBLISHERS TEXT
    );
    CREATE TABLE IF NOT EXISTS JUEGOS_CONSOLAS (
      JUEGO_ID INTEGER,
      CONSOLA_ID INTEGER,
      RUTA_NUBE TEXT DEFAULT '',
      PRIMARY KEY (JUEGO_ID, CONSOLA_ID),
      FOREIGN KEY (JUEGO_ID) REFERENCES JUEGOS(ID),
      FOREIGN KEY (CONSOLA_ID) REFERENCES CONSOLAS(ID)
    );
    """)
    conn.commit()
    agregar_columna_si_no_existe(conn, "CONSOLAS", "NUM_JUEGOS_API", "INTEGER")

def determine_manufacturer(name: str) -> str:
    n = name.lower().strip()
    if 'neo geo' in n: return "SNK"
    if n in ('psp', 'playstation portable'): return "Sony"
    if n in ('ps vita', 'playstation vita'): return "Sony"
    if 'apple ii' in n: return "Apple"
    if n == 'nes' or 'nintendo entertainment system' in n: return "Nintendo"
    if 'classic macintosh' in n or 'macintosh' in n: return "Apple"
    if 'game gear' in n: return "SEGA"
    if n == 'snes' or 'super nintendo' in n or 'super nintendo entertainment system' in n: return "Nintendo"
    if 'gamecube' in n: return "Nintendo"
    if '3do' in n: return "The 3DO Company"
    if 'jaguar' in n: return "Atari"
    if 'commodore' in n or 'amiga' in n: return "Commodore"
    if n == 'genesis' or 'sega genesis' in n or 'mega drive' in n: return "SEGA"
    if n == 'web' or 'browser' in n: return "Web"
    if re.search(r'\bnintendo\b', n) or 'game boy' in n or 'wii' in n: return "Nintendo"
    if 'playstation' in n or re.match(r'^ps[0-9]', n): return "Sony"
    if 'xbox' in n: return "Microsoft"
    if re.search(r'\bsega\b', n) or 'dreamcast' in n or 'megadrive' in n: return "SEGA"
    if 'atari' in n: return "Atari"
    if 'steam deck' in n or ('steam' in n and 'deck' in n): return "Valve"
    if 'oculus' in n or 'quest' in n or 'rift' in n: return "Meta"
    if 'windows' in n or 'win32' in n or 'win64' in n: return "Microsoft"
    if re.search(r'\bmac\s?os\b', n) or 'os x' in n or 'macos' in n: return "Apple"
    if re.search(r'\blinux\b', n) or 'ubuntu' in n or 'debian' in n or 'fedora' in n or 'arch linux' in n or 'centos' in n or 'red hat' in n: return "Linux"
    if 'chrome os' in n or 'chromebook' in n: return "Google"
    if 'android' in n: return "Google"
    if re.search(r'\bios\b', n) or 'ipados' in n or 'tvos' in n or 'watchos' in n: return "Apple"
    if 'fire os' in n: return "Amazon"
    if 'sailfish' in n: return "Jolla"
    if 'tizen' in n: return "Samsung"
    if 'webos' in n: return "LG"
    if 'blackberry' in n: return "BlackBerry"
    if 'raspberry pi' in n: return "Raspberry Pi Foundation"
    if n.strip() == 'pc': return "PC"
    return "Desconocida"

def fetch_consolas_empresas(session, conn):
    url = f"https://api.rawg.io/api/platforms?key={API_KEY}&page_size=100"
    page = 1
    c = conn.cursor()
    while True:
        resp = session.get(f"{url}&page={page}")
        resp.raise_for_status()
        data = resp.json()
        for p in data['results']:
            pid  = p['id']
            name = p['name']
            fabricante = determine_manufacturer(name)
            c.execute("INSERT OR IGNORE INTO EMPRESAS (NOMBRE) VALUES (?)", (fabricante,))
            c.execute("SELECT ID FROM EMPRESAS WHERE NOMBRE=?", (fabricante,))
            empresa_id = c.fetchone()[0]
            c.execute("""
                INSERT OR IGNORE INTO CONSOLAS (ID, NOMBRE, EMPRESA_ID)
                VALUES (?, ?, ?)
            """, (pid, name, empresa_id))
        if not data.get('next'):
            break
        page += 1
        time.sleep(SLEEP_API)
    conn.commit()

def get_num_juegos_api(session, consola_id):
    url = f"https://api.rawg.io/api/games?key={API_KEY}&platforms={consola_id}&page_size=1"
    resp = session.get(url)
    resp.raise_for_status()
    data = resp.json()
    return data.get('count', 0)

def get_game_description(session, juego_id: int) -> str:
    url = f"https://api.rawg.io/api/games/{juego_id}?key={API_KEY}"
    resp = session.get(url)
    if resp.status_code == 200:
        return resp.json().get('description_raw','')
    return ""

def contar_juegos_bbdd(conn, consola_id):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM JUEGOS_CONSOLAS WHERE CONSOLA_ID=?", (consola_id,))
    return cur.fetchone()[0]

def main():
    inicio = time.time()
    conn    = sqlite3.connect("juegos.db")
    session = requests.Session()
    
    crear_base_de_datos(conn)
    fetch_consolas_empresas(session, conn)

    cur = conn.cursor()
    cur.execute("SELECT ID, NOMBRE FROM CONSOLAS")
    consolas = cur.fetchall()

    juegos_totales = 0

    for cid, cname in consolas:
        if cname.strip().lower() in PLATAFORMAS_OMITIDAS:
            print(f"\nConsola omitida por configuración: {cname} (ID {cid})")
            continue

        print(f"\nConsola: {cname} (ID {cid})")
        # Obtener y guardar número de juegos de la API
        try:
            num_juegos_api = get_num_juegos_api(session, cid)
        except Exception as e:
            print(f"  Error obteniendo número de juegos para {cname}: {e}")
            num_juegos_api = None

        cur.execute("UPDATE CONSOLAS SET NUM_JUEGOS_API=? WHERE ID=?", (num_juegos_api, cid))
        conn.commit()

        # Contar juegos en la BBDD para esa consola
        num_juegos_bbdd = contar_juegos_bbdd(conn, cid)
        print(f"  Juegos en BBDD: {num_juegos_bbdd} | Juegos según API: {num_juegos_api}")

        if num_juegos_api is not None and num_juegos_bbdd == num_juegos_api:
            print("  ✔️  La base de datos está sincronizada con la API para esta consola.")
            continue
        else:
            print("  ❗ Diferencia detectada. Descargando e insertando nuevos juegos...")

        # Si la diferencia es mayor de 40, calcular la página de inicio
        start_page = 1
        if num_juegos_api is not None and abs(num_juegos_api - num_juegos_bbdd) > PAGE_SIZE:
            start_page = ceil(num_juegos_bbdd / PAGE_SIZE) + 1
            print(f"  ➡️  Empezando por la página {start_page} para ahorrar llamadas.")

        pages = ceil(min(num_juegos_api or MAX_RESULTS, MAX_RESULTS) / PAGE_SIZE)
        juegos_descargados = 0

        for page in range(start_page, pages + 1):
            url = (
                f"https://api.rawg.io/api/games?key={API_KEY}"
                f"&platforms={cid}&page_size={PAGE_SIZE}&page={page}"
            )
            retries = 0
            while True:
                try:
                    resp = session.get(url)
                    resp.raise_for_status()
                    break
                except HTTPError as err:
                    code = err.response.status_code
                    if code == 404:
                        print("  → 404: fin de datos para esta consola")
                        page = pages + 1
                        break
                    if code == 502 and retries < MAX_RETRIES:
                        retries += 1
                        print(f"  → 502 Bad Gateway, reintentando {retries}/{MAX_RETRIES} en {RETRY_DELAY}s")
                        time.sleep(RETRY_DELAY)
                        continue
                    print(f"  → Error HTTP {code}, saltando consola")
                    page = pages + 1
                    break
                except RequestException as err:
                    print(f"  → Error de red: {err}, saltando consola")
                    page = pages + 1
                    break

            if page > pages:
                break

            data = resp.json()
            batch = data.get('results', [])
            if not batch:
                break

            for j in batch:
                gid   = j["id"]
                name  = j.get("name")
                date  = j.get("released")
                pubs  = ", ".join([p["name"] for p in j.get("publishers", [])])
                desc  = get_game_description(session, gid)
                cur.execute("""
                    INSERT OR IGNORE INTO JUEGOS (ID,NOMBRE,FECHA_LANZAMIENTO,DESCRIPCION,PUBLISHERS)
                    VALUES (?,?,?,?,?)
                """, (gid,name,date,desc,pubs))
                cur.execute("""
                    INSERT OR IGNORE INTO JUEGOS_CONSOLAS (JUEGO_ID, CONSOLA_ID, RUTA_NUBE)
                    VALUES (?, ?, '')
                """, (gid, cid))
                juegos_descargados += 1
                juegos_totales += 1

            conn.commit()
            print(f"  Página {page}: {juegos_descargados} juegos insertados/actualizados para esta consola")
            time.sleep(SLEEP_API)
            if juegos_descargados >= MAX_RESULTS:
                break

        print(f"  Total recolectados en {cname}: {juegos_descargados} juegos")

    session.close()
    conn.close()
    print(f"\n¡Proceso completado! Juegos descargados/actualizados en total: {juegos_totales}")
    print(f"Tiempo total: {time.time() - inicio:.2f} segundos")

if __name__ == "__main__":
    main()
