// app.js
// Small, dependency-free script:
// - renders shared site header and footer
// - toggles mobile nav visibility (aria-friendly)
// - accessible keyboard handling (Escape closes mobile nav)

/* Utility: select single element */
const $ = (sel) => document.querySelector(sel);
/* Utility: select all */
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

document.addEventListener('DOMContentLoaded', () => {
	const isPagesDirectory = window.location.pathname.includes('/pages/');
	const basePath = isPagesDirectory ? '../' : '';
	const currentPage = window.location.pathname.split('/').pop() || 'index.html';

	const navItems = [
		{ href: `${basePath}index.html`, page: 'index.html', label: 'Home' },
		{ href: `${basePath}pages/about.html`, page: 'about.html', label: 'About Us' },
		{ href: `${basePath}pages/classes.html`, page: 'classes.html', label: 'Classes & Schedule' },
		{ href: `${basePath}pages/splendid-china.html`, page: 'splendid-china.html', label: 'Splendid China' },
		{ href: `${basePath}pages/contact.html`, page: 'contact.html', label: 'Contact' }
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
						<a href="${basePath}index.html" class="logo" aria-label="Madison Chinese Dance Academy home">Madison Chinese Dance Academy</a>

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
						<a href="${basePath}pages/tickets.html" class="btn btn-primary header-cta" role="button" aria-label="Purchase Tickets"${ticketsActive}>Purchase Tickets</a>
						<a href="${basePath}pages/donate.html" class="btn btn-secondary header-cta" role="button" aria-label="Donate"${donateActive}>Donate</a>
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
					<p class="footer-copy">© 2026 Madison Chinese Dance Academy</p>
					<p class="footer-contact">Email: ahuan98-dance@yahoo.com</p>
					<p class="footer-contact">Phone: 301.299.1562</p>
				</div>
			</footer>
		`;
	}

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

