import { chromium } from 'playwright';

const browser = await chromium.launch();
const results = [];

for (const width of [1600, 1300, 1200, 1100, 992, 768]) {
	const page = await browser.newPage({ viewport: { width, height: 900 } });
	await page.goto('http://localhost:8765/index.html', { waitUntil: 'networkidle' });
	await page.waitForTimeout(300);
	const state = await page.evaluate(() => {
		const header = document.querySelector('.site-header');
		const inner = document.querySelector('.header-inner');
		const navToggle = document.getElementById('nav-toggle');
		const headerCtas = document.querySelector('.header-ctas');
		const logoFull = document.querySelector('.logo-full-text');
		return {
			collapsed: header?.classList.contains('is-nav-collapsed'),
			scrollWidth: inner?.scrollWidth,
			clientWidth: inner?.clientWidth,
			toggleDisplay: navToggle ? getComputedStyle(navToggle).display : null,
			ctasDisplay: headerCtas ? getComputedStyle(headerCtas).display : null,
			logoFullDisplay: logoFull ? getComputedStyle(logoFull).display : null,
		};
	});
	results.push({ width, ...state });
	await page.close();
}

const resizePage = await browser.newPage({ viewport: { width: 768, height: 900 } });
await resizePage.goto('http://localhost:8765/index.html', { waitUntil: 'networkidle' });
await resizePage.click('#nav-toggle');
await resizePage.waitForTimeout(100);
const menuOpenBefore = await resizePage.evaluate(() =>
	document.getElementById('primary-navigation')?.classList.contains('open')
);
await resizePage.setViewportSize({ width: 1600, height: 900 });
await resizePage.waitForTimeout(300);
const afterResize = await resizePage.evaluate(() => ({
	collapsed: document.querySelector('.site-header')?.classList.contains('is-nav-collapsed'),
	menuOpen: document.getElementById('primary-navigation')?.classList.contains('open'),
}));
results.push({ test: 'resize_close', menuOpenBefore, ...afterResize });

await browser.close();
console.log(JSON.stringify(results, null, 2));
