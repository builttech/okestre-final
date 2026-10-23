"""Render official SVG unchanged; generate Windows, tray and extension sizes."""
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
brand = root / "resources" / "brand"
svg = (brand / "okestre.svg").read_text(encoding="utf-8")
with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(viewport={"width":1024,"height":1024}, device_scale_factor=1)
    page.set_content('<style>body{margin:0}svg{display:block;width:1024px;height:1024px}</style>' + svg)
    page.locator("svg").screenshot(path=str(brand / "okestre-1024.png"), omit_background=True)
    browser.close()
with Image.open(brand / "okestre-1024.png") as source:
    source = source.convert("RGBA")
    for size in (16, 24, 32, 48, 64, 128, 256, 512):
        source.resize((size,size), Image.Resampling.LANCZOS).save(brand / f"okestre-{size}.png")
    source.save(brand / "okestre.ico", sizes=[(s,s) for s in (16,24,32,48,64,128,256)])
    icons = root / "browser-extension" / "gitide-qa-annotator" / "icons"
    icons.mkdir(parents=True,exist_ok=True)
    for size in (16,32,48,128):
        source.resize((size,size), Image.Resampling.LANCZOS).save(icons / f"icon-{size}.png")
print("Official brand icons generated")
