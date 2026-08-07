#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, os, shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def resolve_path(base: Path, value: str) -> Path:
    p = Path(value)
    if p.is_absolute():
        return p
    candidate = (base / p).resolve()
    if candidate.exists():
        return candidate
    return (ROOT / p).resolve()


def load_template_contract(template_name: str) -> dict:
    manifest = load_json(ROOT / 'templates' / 'manifest.json')
    try:
        return manifest['templates'][template_name]
    except KeyError as exc:
        known = ', '.join(sorted(manifest.get('templates', {})))
        raise ValueError(f"Unknown template '{template_name}'. Registered templates: {known}") from exc


def build_html(config_path: Path, output_html: Path) -> tuple[dict, dict]:
    config = load_json(config_path)
    template_name = config['document'].get('template', 'executive-brief')
    contract = load_template_contract(template_name)
    page_count = len(config.get('pages', []))
    minimum, maximum = contract['page_range']
    if not minimum <= page_count <= maximum:
        raise ValueError(
            f"Template '{template_name}' requires {minimum}-{maximum} pages; received {page_count}"
        )
    theme_path = resolve_path(config_path.parent, config['document']['theme'])
    theme = load_json(theme_path)
    if theme.get('palette_ref'):
        palette_path = resolve_path(theme_path.parent, theme['palette_ref'])
        palette = load_json(palette_path)
        theme['colors'] = palette['colors']
        theme['palette'] = palette
    env = Environment(loader=FileSystemLoader(str(ROOT)), undefined=StrictUndefined, autoescape=False)
    css_tpl = env.get_template('assets/theme.css.j2')
    css = css_tpl.render(theme=theme)
    doc_tpl = env.get_template(contract['renderer'])
    html = doc_tpl.render(
        document=config['document'], pages=config['pages'], theme=theme, css=css,
        contract=contract, template_name=template_name,
    )
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(html, encoding='utf-8')
    return config, theme


async def render_browser(html_path: Path, out_dir: Path, stem: str):
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:
        raise RuntimeError(
            "PDF/PNG rendering requires Playwright. Install requirements.txt or use --html-only."
        ) from exc
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / f'{stem}.pdf'
    async with async_playwright() as p:
        executable = os.environ.get('NICE_CHROMIUM_PATH')
        if not executable:
            executable = next((shutil.which(name) for name in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(name)), None)
        launch_args = {'args': ['--no-sandbox']}
        if executable:
            launch_args['executable_path'] = executable
        browser = await p.chromium.launch(**launch_args)
        page = await browser.new_page(viewport={"width": 1404, "height": 993}, device_scale_factor=1)
        await page.set_content(html_path.read_text(encoding='utf-8'), wait_until='networkidle')
        await page.emulate_media(media='print')
        await page.pdf(path=str(pdf_path), print_background=True, prefer_css_page_size=True, margin={"top":"0","right":"0","bottom":"0","left":"0"})
        pages = page.locator('.page')
        count = await pages.count()
        screenshots = []
        for i in range(count):
            path = out_dir / f'{stem}_page{i+1}.png'
            await pages.nth(i).screenshot(path=str(path))
            screenshots.append(path)
        await browser.close()
    return pdf_path, screenshots


async def main_async(args):
    config_path = Path(args.config).resolve()
    out_dir = Path(args.output).resolve()
    stem = args.name or config_path.stem
    html_path = out_dir / f'{stem}.html'
    build_html(config_path, html_path)
    if args.html_only:
        print(json.dumps({"html": str(html_path)}, ensure_ascii=False, indent=2))
        return
    pdf_path, screenshots = await render_browser(html_path, out_dir, stem)
    print(json.dumps({"html": str(html_path), "pdf": str(pdf_path), "screenshots": [str(p) for p in screenshots]}, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser(description='Render registered Nice HTML/PDF/PNG artifacts.')
    ap.add_argument('config')
    ap.add_argument('--output', default=str(ROOT / 'dist'))
    ap.add_argument('--name')
    ap.add_argument(
        '--html-only', action='store_true',
        help='Build the HTML contract without launching Chromium (useful for schema and template smoke tests).',
    )
    args = ap.parse_args()
    asyncio.run(main_async(args))

if __name__ == '__main__':
    main()
