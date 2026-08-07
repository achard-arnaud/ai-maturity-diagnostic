#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, math, os, shutil
from pathlib import Path
from playwright.async_api import async_playwright

MIN_FONT_PX = 12.0  # 9pt at 96 DPI
MIN_PADDING_PX = 12.0  # 9pt

JS = r'''
() => {
  const px = v => parseFloat(v || '0');
  const visible = el => {
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    return cs.display !== 'none' && cs.visibility !== 'hidden' && r.width > 0 && r.height > 0;
  };
  const body = document.body;
  const report = {
    pages: [], violations: [],
    page_contract: {
      min: Number(body.dataset.minPages || 1),
      max: Number(body.dataset.maxPages || 2),
      template: body.dataset.template || 'executive-brief'
    }
  };
  const pages = [...document.querySelectorAll('.page')];
  report.page_count = pages.length;
  for (const [pi, page] of pages.entries()) {
    const pr = page.getBoundingClientRect();
    const pageInfo = { index: pi + 1, width: pr.width, height: pr.height, overlaps: [], overflows: [], out_of_bounds: [], small_fonts: [], low_padding: [] };

    for (const container of page.querySelectorAll('[data-overlap-check]')) {
      const kids = [...container.children].filter(el => el.hasAttribute('data-layout-box') && visible(el));
      for (let i=0; i<kids.length; i++) {
        const a = kids[i].getBoundingClientRect();
        for (let j=i+1; j<kids.length; j++) {
          const b = kids[j].getBoundingClientRect();
          const iw = Math.max(0, Math.min(a.right,b.right)-Math.max(a.left,b.left));
          const ih = Math.max(0, Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top));
          if (iw > 1 && ih > 1) pageInfo.overlaps.push({a:i,b:j,area:iw*ih});
        }
      }
    }

    for (const el of page.querySelectorAll('[data-no-overflow]')) {
      if (!visible(el)) continue;
      if (el.scrollHeight > el.clientHeight + 1 || el.scrollWidth > el.clientWidth + 1) {
        pageInfo.overflows.push({tag: el.tagName, cls: el.className, scrollHeight: el.scrollHeight, clientHeight: el.clientHeight, scrollWidth: el.scrollWidth, clientWidth: el.clientWidth});
      }
    }

    for (const el of page.querySelectorAll('*')) {
      if (!visible(el)) continue;
      const r = el.getBoundingClientRect();
      if (r.left < pr.left - 1 || r.top < pr.top - 1 || r.right > pr.right + 1 || r.bottom > pr.bottom + 1) {
        if (!['HTML','BODY'].includes(el.tagName)) pageInfo.out_of_bounds.push({tag: el.tagName, cls: el.className, rect: {left:r.left, top:r.top, right:r.right, bottom:r.bottom}});
      }
      const text = (el.childNodes.length === 1 && el.childNodes[0].nodeType === Node.TEXT_NODE) ? el.textContent.trim() : '';
      if (text) {
        const fs = px(getComputedStyle(el).fontSize);
        if (fs < 12 - 0.05) pageInfo.small_fonts.push({tag: el.tagName, cls: el.className, fontSize: fs, text: text.slice(0,80)});
      }
    }

    for (const el of page.querySelectorAll('[data-card]')) {
      const cs = getComputedStyle(el);
      const vals = [px(cs.paddingTop), px(cs.paddingRight), px(cs.paddingBottom), px(cs.paddingLeft)];
      if (Math.min(...vals) < 12 - 0.05) pageInfo.low_padding.push({tag:el.tagName, cls:el.className, padding:vals});
    }

    report.pages.push(pageInfo);
  }
  return report;
}
'''

async def qa(html: Path, screenshot_dir: Path | None = None):
    async with async_playwright() as p:
        executable = os.environ.get('NICE_CHROMIUM_PATH')
        if not executable:
            executable = next((shutil.which(name) for name in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(name)), None)
        launch_args = {'args': ['--no-sandbox']}
        if executable:
            launch_args['executable_path'] = executable
        browser = await p.chromium.launch(**launch_args)
        page = await browser.new_page(viewport={"width": 1404, "height": 993}, device_scale_factor=1)
        await page.set_content(html.read_text(encoding='utf-8'), wait_until='networkidle')
        result = await page.evaluate(JS)
        if screenshot_dir:
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            loc = page.locator('.page')
            for i in range(await loc.count()):
                await loc.nth(i).screenshot(path=str(screenshot_dir / f'qa_page{i+1}.png'))
        await browser.close()
    summary = {"page_count": result["page_count"], "overlaps":0, "overflows":0, "out_of_bounds":0, "small_fonts":0, "low_padding":0}
    for p in result['pages']:
        for k in ['overlaps','overflows','out_of_bounds','small_fonts','low_padding']:
            summary[k] += len(p[k])
    result['summary'] = summary
    contract = result['page_contract']
    page_count_ok = contract['min'] <= result['page_count'] <= contract['max']
    result['pass'] = page_count_ok and all(summary[k] == 0 for k in ['overlaps','overflows','out_of_bounds','small_fonts','low_padding'])
    result['summary']['page_contract_ok'] = page_count_ok
    return result

async def main_async(args):
    result = await qa(Path(args.html), Path(args.screenshots) if args.screenshots else None)
    out = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result['summary'] | {"pass": result['pass']}, ensure_ascii=False, indent=2))
    if not result['pass']:
        raise SystemExit(2)


def main():
    ap = argparse.ArgumentParser(description='DOM-based visual QA for registered Nice layouts.')
    ap.add_argument('html')
    ap.add_argument('--report', required=True)
    ap.add_argument('--screenshots')
    args = ap.parse_args()
    asyncio.run(main_async(args))

if __name__ == '__main__':
    main()
