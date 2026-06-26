"""Funções de download e descompactação dos arquivos brutos.

Tudo vai para data/raw. Os arquivos não são versionados (.gitignore). Cada função
pula o download se o arquivo já existe, para permitir reexecução barata do notebook.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import requests
from tqdm import tqdm

from . import config

# User-Agent "de navegador": alguns portais gov.br rejeitam o default do requests.
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AtlasSolarBR/1.0; +pesquisa academica)"
}


def baixar_arquivo(url: str, destino: Path, *, forcar: bool = False) -> Path:
    """Baixa `url` para `destino` com barra de progresso. Pula se já existir."""
    destino = Path(destino)
    if destino.exists() and not forcar:
        print(f"[cache] {destino.name} já existe — pulando download.")
        return destino

    destino.parent.mkdir(parents=True, exist_ok=True)
    print(f"[down ] {url}")
    with requests.get(url, headers=_HEADERS, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        tmp = destino.with_suffix(destino.suffix + ".part")
        with open(tmp, "wb") as f, tqdm(
            total=total, unit="B", unit_scale=True, desc=destino.name, leave=False
        ) as barra:
            for bloco in r.iter_content(chunk_size=1 << 16):
                f.write(bloco)
                barra.update(len(bloco))
        tmp.replace(destino)  # escrita atômica: só vira o arquivo final se completou
    print(f"[ok   ] {destino.name} ({destino.stat().st_size/1e6:.1f} MB)")
    return destino


def descompactar(zip_path: Path, destino_dir: Path | None = None) -> list[Path]:
    """Extrai um .zip e devolve a lista de arquivos extraídos."""
    zip_path = Path(zip_path)
    destino_dir = Path(destino_dir or zip_path.with_suffix(""))
    destino_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(destino_dir)
        nomes = z.namelist()
    extraidos = [destino_dir / n for n in nomes]
    print(f"[unzip] {zip_path.name} -> {len(extraidos)} arquivo(s) em {destino_dir.name}/")
    return extraidos


def baixar_inpe(variavel: str = "gti", *, forcar: bool = False) -> list[Path]:
    """Baixa e descompacta uma variável do Atlas INPE (default: GTI/plano inclinado)."""
    url = config.LABREN_CSV[variavel]
    zip_dest = config.RAW / f"inpe_{variavel}.zip"
    baixar_arquivo(url, zip_dest, forcar=forcar)
    return descompactar(zip_dest, config.INTERIM / f"inpe_{variavel}")


def baixar_aneel(*, forcar: bool = False) -> list[Path]:
    """Baixa e descompacta a relação de empreendimentos de GD da ANEEL (~122 MB)."""
    zip_dest = config.RAW / "aneel_gd.zip"
    baixar_arquivo(config.ANEEL_GD_ZIP, zip_dest, forcar=forcar)
    return descompactar(zip_dest, config.INTERIM / "aneel_gd")
