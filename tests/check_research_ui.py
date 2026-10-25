"""Optional browser checks: python tests/check_research_ui.py (requires Playwright)."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
import tempfile
from threading import Thread

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright, expect
from research_service.core import ROOT, Store
from research_service.server import make_server
from research_service.worker import Worker


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass


def main():
    with tempfile.TemporaryDirectory() as tmp:
        store = Store(Path(tmp) / 'jobs.sqlite3')
        alice, bob = store.add_user('alice'), store.add_user('bob')
        local = make_server(store, 0)
        static = ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
        worker = Worker(store)
        for server in (local,static): Thread(target=server.serve_forever,daemon=True).start()
        worker.start()
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True,args=['--no-sandbox'])
                page = browser.new_page(viewport={'width':1440,'height':1100},reduced_motion='reduce')
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(f'http://127.0.0.1:{static.server_port}/research.html')
                assert not page.locator('#login-panel').is_visible()
                page.locator('#submit-research').click()
                page.wait_for_selector('.report-claims li')
                assert page.locator('.report-claims>li').count() == 10
                assert 'Hermes 미실행' in page.locator('.report-label').inner_text()
                page.locator('#domain').select_option('entertainment')
                page.locator('#submit-research').click()
                page.wait_for_function("document.querySelector('#report h3').textContent.includes('연예')")
                assert page.locator('.report-claims>li').count() == 10
                with page.expect_download() as download:
                    page.locator('#download-report').click()
                data = json.loads(Path(download.value.path()).read_text())
                assert data['hermes_executed'] is False and len(data['claims']) == 10
                for width in (1440,768,481,390,320):
                    page.set_viewport_size({'width':width,'height':1000})
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
                    page.locator('.service-nav summary').click()
                    link = page.locator('.service-nav a[href="research.html"]')
                    assert link.is_visible()
                    bounds = link.bounding_box()
                    assert bounds['x'] >= 0 and bounds['x']+bounds['width'] <= width, width
                    page.locator('.service-nav summary').press('Escape')
                output = os.environ.get('SCREENSHOT_DIR')
                if output:
                    Path(output).mkdir(parents=True,exist_ok=True)
                    page.set_viewport_size({'width':1440,'height':1100})
                    page.screenshot(path=str(Path(output)/'research-desktop.png'),full_page=True)
                    page.set_viewport_size({'width':390,'height':900})
                    page.screenshot(path=str(Path(output)/'research-mobile.png'),full_page=True)
                # Text and links from data must never become executable HTML.
                fixture = json.loads((ROOT/'data/news-case-studies-2026-10-25.json').read_text())
                fixture['claims'][0]['text'] = '<img src=x onerror="window.injected=true">'
                fixture['sources'][0]['url'] = 'javascript:window.injected=true'
                page.route('**/data/news-case-studies-2026-10-25.json', lambda route:route.fulfill(json=fixture))
                page.locator('#domain').select_option('politics')
                page.locator('#submit-research').click()
                page.wait_for_function("document.querySelector('.report-claims').textContent.includes('<img')")
                assert not page.locator('#report img').count()
                assert not page.locator('#report a[href^="javascript:"]').count()
                assert page.evaluate('window.injected') is None
                page.unroute('**/data/news-case-studies-2026-10-25.json')
                base = f'http://127.0.0.1:{local.server_port}'
                page.goto(base+'/research.html')
                page.wait_for_selector('#login-panel',state='visible')
                page.locator('#invite-token').fill(alice)
                page.locator('#login-form button').click()
                page.wait_for_selector('#account',state='visible')
                page.locator('#submit-research').click()
                page.wait_for_selector('.report-claims li')
                assert page.locator('#history-list button').count() == 1
                with page.expect_download() as download:
                    page.locator('#download-report').click()
                job = json.loads(Path(download.value.path()).read_text())
                assert job['state'] == 'completed' and len(job['result']['claims']) == 10
                page.reload()
                page.wait_for_selector('#account',state='visible')
                page.locator('#history-list button').click()
                page.wait_for_selector('.report-claims li')
                page.locator('#logout').click()
                page.wait_for_selector('#login-panel',state='visible')
                assert not page.locator('#report').is_visible()
                page.locator('#invite-token').fill(bob)
                page.locator('#login-form button').click()
                expect(page.locator('#user-name')).to_contain_text('bob')
                assert page.locator('#history-list button').count() == 0
                response = page.request.get(base+'/api/research/'+job['id']+'/download')
                assert response.status == 404
                assert not errors, errors
                browser.close()
                print('Static samples, exports, 5 viewport widths, menus, XSS handling, local login, saved history, reload, logout and user separation passed.')
        finally:
            worker.close()
            for server in (local,static): server.shutdown();server.server_close()


if __name__ == '__main__': main()
