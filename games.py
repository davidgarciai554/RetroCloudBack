import requests
import sqlite3
import time
import re
from math import ceil

API_KEY     = "80eee4b42c7e4433b572c0dd535696dd"
MAX_RESULTS = 1   # Nº máximo de juegos por consola
PAGE_SIZE   = 40   # Máx por página que permite RAWG
DB_NAME     = "juegos.db"
SLEEP_API   = 0.2  # Pausa entre peticiones (juegos y descripciones)

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
      PRIMARY KEY (JUEGO_ID, CONSOLA_ID),
      FOREIGN KEY (JUEGO_ID) REFERENCES JUEGOS(ID),
      FOREIGN KEY (CONSOLA_ID) REFERENCES CONSOLAS(ID)
    );
    """)
    conn.commit()

def determine_manufacturer(name: str) -> str:
    n = name.lower().strip()

    # Agregados según tu lista
    if 'neo geo' in n:
        return "SNK"
    if n in ('psp', 'playstation portable'):
        return "Sony"
    if n in ('ps vita', 'playstation vita'):
        return "Sony"
    if 'apple ii' in n:
        return "Apple"
    if n == 'nes' or 'nintendo entertainment system' in n:
        return "Nintendo"
    if 'classic macintosh' in n or 'macintosh' in n:
        return "Apple"
    if 'game gear' in n:
        return "SEGA"
    if n == 'snes' or 'super nintendo' in n or 'super nintendo entertainment system' in n:
        return "Nintendo"
    if 'gamecube' in n:
        return "Nintendo"
    if '3do' in n:
        return "The 3DO Company"
    if 'jaguar' in n:
        return "Atari"
    if 'commodore' in n or 'amiga' in n:
        return "Commodore"
    if n == 'genesis' or 'sega genesis' in n or 'mega drive' in n:
        return "SEGA"
    if n == 'web' or 'browser' in n:
        return "Web"

    # Consolas clásicas
    if re.search(r'\bnintendo\b', n) or 'game boy' in n or 'wii' in n:
        return "Nintendo"
    if 'playstation' in n or re.match(r'^ps[0-9]', n):
        return "Sony"
    if 'xbox' in n:
        return "Microsoft"
    if re.search(r'\bsega\b', n) or 'dreamcast' in n or 'megadrive' in n:
        return "SEGA"
    if 'atari' in n:
        return "Atari"
    if 'steam deck' in n or ('steam' in n and 'deck' in n):
        return "Valve"
    if 'oculus' in n or 'quest' in n or 'rift' in n:
        return "Meta"

    # Sistemas operativos de sobremesa/PC
    if 'windows' in n or 'win32' in n or 'win64' in n:
        return "Microsoft"
    if re.search(r'\bmac\s?os\b', n) or 'os x' in n or 'macos' in n:
        return "Apple"
    if re.search(r'\blinux\b', n) \
       or 'ubuntu' in n or 'debian' in n or 'fedora' in n \
       or 'arch linux' in n or 'centos' in n or 'red hat' in n:
        return "Linux"
    if 'chrome os' in n or 'chromebook' in n:
        return "Google"

    # Sistemas operativos móviles/embebidos
    if 'android' in n:
        return "Google"
    if re.search(r'\bios\b', n) or 'ipados' in n or 'tvos' in n or 'watchos' in n:
        return "Apple"
    if 'fire os' in n:
        return "Amazon"
    if 'sailfish' in n:
        return "Jolla"
    if 'tizen' in n:
        return "Samsung"
    if 'webos' in n:
        return "LG"
    if 'blackberry' in n:
        return "BlackBerry"
    if 'raspberry pi' in n:
        return "Raspberry Pi Foundation"

    # PC genérico
    if n == 'pc':
        return "PC"

    # Heurística por defecto
    return "Desconocida"
    """
    Devuelve el fabricante o sistema operativo más probable según patrones en el nombre.
    Cubre consolas, PCs y múltiples sistemas operativos (Windows, Linux, macOS, Android…).
    """
    n = name.lower()

    # Consolas clásicas
    if re.search(r'\bnintendo\b', n) or 'game boy' in n or 'wii' in n:
        return "Nintendo"
    if 'playstation' in n or re.match(r'^ps[0-9]', n):
        return "Sony"
    if 'xbox' in n:
        return "Microsoft"
    if re.search(r'\bsega\b', n) or 'dreamcast' in n or 'megadrive' in n:
        return "SEGA"
    if 'atari' in n:
        return "Atari"
    if 'steam deck' in n or ('steam' in n and 'deck' in n):
        return "Valve"
    if 'oculus' in n or 'quest' in n or 'rift' in n:
        return "Meta"

    # Sistemas operativos de sobremesa/PC
    if 'windows' in n or 'win32' in n or 'win64' in n:
        return "Microsoft"
    if re.search(r'\bmac\s?os\b', n) or 'os x' in n or 'macos' in n:
        return "Apple"
    if re.search(r'\blinux\b', n) \
       or 'ubuntu' in n or 'debian' in n or 'fedora' in n \
       or 'arch linux' in n or 'centos' in n or 'red hat' in n:
        return "Linux"
    if 'chrome os' in n or 'chromebook' in n:
        return "Google"
    if 'android' in n:
        return "Google"
    if re.search(r'\bios\b', n) or 'ipados' in n or 'tvos' in n or 'watchos' in n:
        return "Apple"
    if 'fire os' in n:
        return "Amazon"
    if 'sailfish' in n:
        return "Jolla"
    if 'tizen' in n:
        return "Samsung"
    if 'webos' in n:
        return "LG"
    if 'blackberry' in n:
        return "BlackBerry"
    if 'raspberry pi' in n:
        return "Raspberry Pi Foundation"

    # PC genérico
    if n.strip() == 'pc':
        return "PC"

    # Heurística por defecto
    return "Desconocida"

def fetch_consolas_empresas(session):
    """Trae de RAWG todas las consolas y su fabricante según nombre."""
    url = f"https://api.rawg.io/api/platforms?key={API_KEY}&page_size=100"
    consolas_empresas = {}
    plataformas_info  = {}
    page = 1
    while True:
        resp = session.get(f"{url}&page={page}")
        resp.raise_for_status()
        data = resp.json()
        for p in data['results']:
            pid  = p['id']
            name = p['name']
            plataformas_info[pid]  = name
            consolas_empresas[pid] = determine_manufacturer(name)
        if not data.get('next'):
            break
        page += 1
        time.sleep(SLEEP_API)
    return consolas_empresas, plataformas_info

def get_game_description(session, juego_id: int) -> str:
    url = f"https://api.rawg.io/api/games/{juego_id}?key={API_KEY}"
    resp = session.get(url)
    if resp.status_code == 200:
        return resp.json().get('description_raw','')
    return ""

def main():
    # 1) Preparar BD y sesión HTTP
    conn = sqlite3.connect(DB_NAME)
    crear_base_de_datos(conn)
    session = requests.Session()

    # 2) Sincronizar CONSOLAS ↔ EMPRESAS
    ce, pi = fetch_consolas_empresas(session)
    cur = conn.cursor()
    for cid, cname in pi.items():
        # insertar empresa
        empresa = ce[cid]
        cur.execute("INSERT OR IGNORE INTO EMPRESAS (NOMBRE) VALUES (?)", (empresa,))
        cur.execute("SELECT ID FROM EMPRESAS WHERE NOMBRE = ?", (empresa,))
        eid = cur.fetchone()[0]
        # insertar consola
        cur.execute("""
          INSERT OR IGNORE INTO CONSOLAS (ID,NOMBRE,EMPRESA_ID)
          VALUES (?,?,?)
        """, (cid, cname, eid))
    conn.commit()

    # 3) Cargar en memoria IDs de juegos existentes
    cur.execute("SELECT ID FROM JUEGOS")
    existing_ids = {row[0] for row in cur.fetchall()}

    # 4) Por cada consola en BD, descargar y preparar lotes
    cur.execute("SELECT ID, NOMBRE FROM CONSOLAS")
    consolas = cur.fetchall()
    for cid, cname in consolas:
        print(f"\nConsola: {cname} (ID {cid}) → max {MAX_RESULTS} juegos")
        # calculamos cuántas páginas necesitamos
        to_fetch = min(MAX_RESULTS, PAGE_SIZE)
        pages = 1 if MAX_RESULTS <= PAGE_SIZE else ceil(MAX_RESULTS / PAGE_SIZE)

        todos = []
        for page in range(1, pages + 1):
            url = (f"https://api.rawg.io/api/games?key={API_KEY}"
                   f"&platforms={cid}&page_size={to_fetch}&page={page}")
            resp = session.get(url)
            resp.raise_for_status()
            data = resp.json()
            batch = data.get('results', [])
            if not batch:
                break
            todos.extend(batch)
            time.sleep(SLEEP_API)
            if len(todos) >= MAX_RESULTS:
                break
        todos = todos[:MAX_RESULTS]
        print(f"  Encontrados: {len(todos)} juegos")

        juegos_ins = []
        jc_ins    = []
        for g in todos:
            jid = g['id']
            if jid in existing_ids:
                continue
            name = g.get('name','')
            rel  = g.get('released','')
            pubs = ','.join(p['name'] for p in g.get('publishers',[]))
            desc = get_game_description(session, jid)
            time.sleep(SLEEP_API)

            juegos_ins.append((jid, name, rel, desc, pubs))
            jc_ins.append((jid, cid))
            existing_ids.add(jid)

        # 5) Insertar lotes
        if juegos_ins:
            cur.executemany("""
              INSERT INTO JUEGOS
              (ID,NOMBRE,FECHA_LANZAMIENTO,DESCRIPCION,PUBLISHERS)
              VALUES (?,?,?,?,?)
            """, juegos_ins)
        if jc_ins:
            cur.executemany("""
              INSERT INTO JUEGOS_CONSOLAS (JUEGO_ID,CONSOLA_ID) VALUES (?,?)
            """, jc_ins)
        conn.commit()
        print(f"  Insertados: {len(juegos_ins)} nuevos juegos")

    # 6) Cerrar recursos
    conn.close()
    session.close()
    print("\n¡Proceso completado con optimizaciones!")

if __name__ == "__main__":
    main()
