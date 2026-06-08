import importlib.util
import pkgutil
import os
from pathlib import Path

def discover_scrapers():
    scrapers = []
    folder = Path(__file__).parent
    for mod in pkgutil.iter_modules([str(folder)]):
        if mod.name.startswith('scrapers_') and mod.name not in ('scrapers_index',):
            m = importlib.import_module(mod.name)
            if hasattr(m, 'scrape'):
                scrapers.append((mod.name, m.scrape))
    return scrapers
