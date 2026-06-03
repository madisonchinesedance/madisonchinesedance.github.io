// app.js
// Small, dependency-free script:
// - loads editable site/page copy from JSON files
// - renders shared site header and footer
// - toggles mobile nav visibility (aria-friendly)
// - accessible keyboard handling (Escape closes mobile nav)

/* Utility: select single element */
const $ = (sel) => document.querySelector(sel);
/* Utility: select all */
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

function escapeHtml(value) {
	return String(value)
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;')
		.replace(/'/g, '&#39;');
}

async function loadJson(path) {
	try {
		const response = await fetch(path);
		if (!response.ok) throw new Error(`Could not load ${path}`);
		return await response.json();
	} catch (error) {
		console.warn(error);
		return {};
	}
}

function renderMultiline(value) {
	return escapeHtml(value)
		.split(/\n{2,}/)
		.map((paragraph) => paragraph.trim().replace(/\n/g, '<br>'))
		.filter(Boolean)
		.map((paragraph) => `<p>${paragraph}</p>`)
		.join('');
}

function applyJsonContent(content) {
	$$('[data-json]').forEach((element) => {
		const key = element.getAttribute('data-json');
		if (!key || content[key] === undefined) return;

		const value = content[key];
		const attr = element.getAttribute('data-json-attr');
		const hrefKey = element.getAttribute('data-json-href');

		if (attr) {
			element.setAttribute(attr, value);
		} else if (element.hasAttribute('data-json-multiline')) {
			element.innerHTML = renderMultiline(value);
		} else {
			element.textContent = value;
		}

		if (hrefKey && content[hrefKey] !== undefined) {
			element.setAttribute('href', content[hrefKey]);
		}
	});
}

document.addEventListener('DOMContentLoaded', async () => {
	const isPagesDirectory = window.location.pathname.includes('/pages/');
	const basePath = isPagesDirectory ? '../' : '';
	const currentPage = window.location.pathname.split('/').pop() || 'index.html';
	const pageContentFile = document.body.getAttribute('data-content-file');
	const [siteContent, pageContent] = await Promise.all([
		loadJson(`${basePath}content/site.json`),
		pageContentFile ? loadJson(`${basePath}content/${pageContentFile}.json`) : Promise.resolve({})
	]);
	const content = { ...siteContent, ...pageContent };

	const navItems = [
		{ href: `${basePath}index.html`, page: 'index.html', label: content.navHome || 'Home' },
		{ href: `${basePath}pages/about.html`, page: 'about.html', label: content.navAbout || 'About Us' },
		{ href: `${basePath}pages/classes.html`, page: 'classes.html', label: content.navClasses || 'Classes & Schedule' },
		{ href: `${basePath}pages/splendid-china.html`, page: 'splendid-china.html', label: content.navSplendid || 'Splendid China' },
		{ href: `${basePath}pages/contact.html`, page: 'contact.html', label: content.navContact || 'Contact' }
	];

	function navLink(item) {
		const isActive = currentPage === item.page;
		const activeClass = isActive ? ' active' : '';
		const currentAttr = isActive ? ' aria-current="page"' : '';
		return `<li><a href="${item.href}" class="nav-link${activeClass}"${currentAttr}>${item.label}</a></li>`;
	}

	function renderHeader() {
		const mount = $('[data-site-header]');
		if (!mount) return;

		const ticketsActive = currentPage === 'tickets.html' ? ' aria-current="page"' : '';
		const donateActive = currentPage === 'donate.html' ? ' aria-current="page"' : '';

		mount.outerHTML = `
			<header class="site-header" role="banner">
				<div class="container header-inner">
					<div class="header-left">
						<a href="${basePath}index.html" class="logo" aria-label="${escapeHtml(content.logoText || 'Madison Chinese Dance Academy')} home">${escapeHtml(content.logoText || 'Madison Chinese Dance Academy')}</a>

						<div class="header-controls">
							<button id="nav-toggle" class="nav-toggle" aria-controls="primary-navigation" aria-expanded="false" aria-label="Open navigation">
								<svg width="24" height="18" viewBox="0 0 24 18" aria-hidden="true" focusable="false">
									<rect width="24" height="2" y="0" rx="1"></rect>
									<rect width="24" height="2" y="8" rx="1"></rect>
									<rect width="24" height="2" y="16" rx="1"></rect>
								</svg>
							</button>
						</div>

						<nav id="primary-navigation" class="primary-nav" aria-label="Primary navigation">
							<ul class="nav-list">
								${navItems.map(navLink).join('')}
							</ul>
						</nav>
					</div>

					<div class="header-ctas">
						<a href="${basePath}${content.ctaTicketsHref || 'pages/tickets.html'}" class="btn btn-primary header-cta" role="button" aria-label="${escapeHtml(content.ctaTickets || 'Purchase Tickets')}"${ticketsActive}>${escapeHtml(content.ctaTickets || 'Purchase Tickets')}</a>
						<a href="${basePath}${content.ctaDonateHref || 'pages/donate.html'}" class="btn btn-secondary header-cta" role="button" aria-label="${escapeHtml(content.ctaDonate || 'Donate')}"${donateActive}>${escapeHtml(content.ctaDonate || 'Donate')}</a>
					</div>
				</div>
			</header>
		`;
	}

	function renderFooter() {
		const mount = $('[data-site-footer]');
		if (!mount) return;

		mount.outerHTML = `
			<footer class="site-footer" role="contentinfo">
				<div class="container footer-inner">
					<p class="footer-copy">${escapeHtml(content.footerCopy || '© 2026 Madison Chinese Dance Academy')}</p>
					<p class="footer-contact">Email: ${escapeHtml(content.footerEmail || 'ahuan98-dance@yahoo.com')}</p>
					<p class="footer-contact">Phone: ${escapeHtml(content.footerPhone || '301.299.1562')}</p>
				</div>
			</footer>
		`;
	}

	applyJsonContent(content);
	renderHeader();
	renderFooter();

	// Elements
	const navToggle = $('#nav-toggle');
	const primaryNav = $('#primary-navigation');

	// NAVIGATION: toggle mobile menu
	if (navToggle && primaryNav) {
		navToggle.addEventListener('click', () => {
			const expanded = navToggle.getAttribute('aria-expanded') === 'true';
			navToggle.setAttribute('aria-expanded', String(!expanded));
			primaryNav.classList.toggle('open');

			// Update accessible label for toggle
			navToggle.setAttribute('aria-label', expanded ? 'Open navigation' : 'Close navigation');
		});

		// Close mobile nav when any nav link is clicked (improves UX on small screens)
		$$('.nav-link').forEach(link => {
			link.addEventListener('click', () => {
				if (primaryNav.classList.contains('open')) {
					primaryNav.classList.remove('open');
					navToggle.setAttribute('aria-expanded', 'false');
					navToggle.setAttribute('aria-label', 'Open navigation');
				}
			});
		});

		// Close the menu with Escape key
		document.addEventListener('keydown', (e) => {
			if (e.key === 'Escape' && primaryNav.classList.contains('open')) {
				primaryNav.classList.remove('open');
				navToggle.setAttribute('aria-expanded', 'false');
				navToggle.focus();
			}
		});

		// If the viewport becomes wide while nav was open, ensure it's closed
		let resizeTimeout;
		window.addEventListener('resize', () => {
			clearTimeout(resizeTimeout);
			resizeTimeout = setTimeout(() => {
				if (window.innerWidth > 880 && primaryNav.classList.contains('open')) {
					primaryNav.classList.remove('open');
					navToggle.setAttribute('aria-expanded', 'false');
				}
			}, 150);
		});
	}
});

