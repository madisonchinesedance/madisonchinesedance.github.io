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

function getPageId() {
    const path = window.location.pathname;
    if (!path.includes('/pages/')) {
        return 'index.html';
    }
    let pagePath = path.substring(path.indexOf('/pages/') + 7);
    if (pagePath === '' || pagePath.endsWith('/')) {
        pagePath += 'index.html';
    }
    return pagePath;
}

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
	const basePath = isPagesDirectory ? '../../' : '';
	const currentPage = getPageId();
	const pageContentFile = document.body.getAttribute('data-content-file');
	const [siteContent, pageContent] = await Promise.all([
		loadJson(`${basePath}content/site.json`),
		pageContentFile ? loadJson(`${basePath}content/${pageContentFile}.json`) : Promise.resolve({})
	]);
	const content = { ...siteContent, ...pageContent };

	const splendidYearItems = ['2026', '2025', '2024', '2023', '2022', '2021', '2020'].map((year) => ({
		href: year === '2026' ? `${basePath}pages/splendid-china/` : `${basePath}pages/splendid-china/splendid-china-${year}.html`,
		page: year === '2026' ? 'splendid-china/index.html' : `splendid-china/splendid-china-${year}.html`,
		label: `Splendid China ${year}`
	}));

	const navItems = [
		{ href: `${basePath}index.html`, page: 'index.html', label: content.navHome || 'Home' },
		{
			label: content.navAbout || 'About Us',
			items: [
				{ href: `${basePath}pages/about/`, page: 'about/index.html', label: content.navAbout || 'About Us' },
				{ href: `${basePath}pages/about/contact.html`, page: 'about/contact.html', label: content.navContact || 'Contact' }
			]
		},
		{
			label: 'Community',
			items: [
				{ href: `${basePath}pages/community/events.html`, page: 'community/events.html', label: 'Events' },
				{ href: `${basePath}pages/classes/services.html`, page: 'classes/services.html', label: 'Services' }
			]
		},
		{
			label: 'Programs',
			items: [
				{ href: `${basePath}pages/classes/dance-classes.html`, page: 'classes/dance-classes.html', label: 'Dance Classes' },
			]
		},
        { href: `${basePath}pages/community/gallery.html`, page: 'community/gallery.html', label: 'Gallery' },
		{ label: content.navSplendid || 'Splendid China', items: splendidYearItems }
	];

	function navLink(item) {
		const isActive = currentPage === item.page;
		const activeClass = isActive ? ' active' : '';
		const currentAttr = isActive ? ' aria-current="page"' : '';
		return `<li class="nav-item"><a href="${item.href}" class="nav-link${activeClass}"${currentAttr}>${escapeHtml(item.label)}</a></li>`;
	}

	function navMenu(item, index) {
		if (!item.items) return navLink(item);

		const isActive = item.items.some((subItem) => currentPage === subItem.page);
		const activeClass = isActive ? ' active' : '';
		const menuId = `nav-menu-${index}`;

		return `
			<li class="nav-item nav-item-dropdown">
				<button class="nav-link nav-menu-toggle${activeClass}" type="button" aria-expanded="false" aria-controls="${menuId}">
					${escapeHtml(item.label)}
					<svg class="nav-caret" width="14" height="14" viewBox="0 0 20 20" aria-hidden="true" focusable="false">
						<path d="M5.5 7.5 10 12l4.5-4.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path>
					</svg>
				</button>
				<ul id="${menuId}" class="nav-dropdown" aria-label="${escapeHtml(item.label)} submenu">
					${item.items.map(navLink).join('')}
				</ul>
			</li>
		`;
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
						<a href="${basePath}index.html" class="logo" aria-label="${escapeHtml(content.logoText || 'Madison Chinese Dance Academy')} home">
							<span class="logo-full-text">${escapeHtml(content.logoText || 'Madison Chinese Dance Academy')}</span>
							<span class="logo-short-text">MCDA</span>
						</a>
					</div>

					<div class="header-controls">
						<nav id="primary-navigation" class="primary-nav" aria-label="Primary navigation">
							<ul class="nav-list">
								${navItems.map(navMenu).join('')}
								<li class="nav-cta-list">
									<a href="${basePath}${content.ctaTicketsHref || 'pages/tickets.html'}" class="btn btn-primary header-cta" role="button" aria-label="${escapeHtml(content.ctaTickets || 'Purchase Tickets')}"${ticketsActive}>${escapeHtml(content.ctaTickets || 'Purchase Tickets')}</a>
									<a href="${basePath}${content.ctaDonateHref || 'pages/donate.html'}" class="btn btn-secondary header-cta" role="button" aria-label="${escapeHtml(content.ctaDonate || 'Donate')}"${donateActive}>${escapeHtml(content.ctaDonate || 'Donate')}</a>
								</li>
							</ul>
						</nav>

						<button id="nav-toggle" class="nav-toggle" aria-controls="primary-navigation" aria-expanded="false" aria-label="Open navigation">
							<svg width="24" height="18" viewBox="0 0 24 18" aria-hidden="true" focusable="false">
								<rect width="24" height="2" y="0" rx="1"></rect>
								<rect width="24" height="2" y="8" rx="1"></rect>
								<rect width="24" height="2" y="16" rx="1"></rect>
							</svg>
						</button>
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
	const dropdownToggles = $$('.nav-menu-toggle');

	function closeDropdowns(exceptToggle = null) {
		dropdownToggles.forEach((toggle) => {
			if (toggle === exceptToggle) return;
			toggle.setAttribute('aria-expanded', 'false');
			toggle.closest('.nav-item-dropdown')?.classList.remove('open');
		});
	}

	dropdownToggles.forEach((toggle) => {
		toggle.addEventListener('click', () => {
			const expanded = toggle.getAttribute('aria-expanded') === 'true';
			closeDropdowns(toggle);
			toggle.setAttribute('aria-expanded', String(!expanded));
			toggle.closest('.nav-item-dropdown')?.classList.toggle('open', !expanded);
		});
	});

	document.addEventListener('click', (e) => {
		if (!e.target.closest('.nav-item-dropdown')) closeDropdowns();
	});

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
				if (link.classList.contains('nav-menu-toggle')) return;

				if (primaryNav.classList.contains('open')) {
					primaryNav.classList.remove('open');
					navToggle.setAttribute('aria-expanded', 'false');
					navToggle.setAttribute('aria-label', 'Open navigation');
				}
				closeDropdowns();
			});
		});

		// Close the menu with Escape key
		document.addEventListener('keydown', (e) => {
			if (e.key === 'Escape') closeDropdowns();

			if (e.key === 'Escape' && primaryNav.classList.contains('open')) {
				primaryNav.classList.remove('open');
				navToggle.setAttribute('aria-expanded', 'false');
				navToggle.focus();
			}
		});
	}

	const galleryContainer = $('.gallery-container');
	if (galleryContainer) {
		const galleryWrapper = galleryContainer.querySelector('.gallery-wrapper');
		const prevButton = galleryContainer.querySelector('.prev');
		const nextButton = galleryContainer.querySelector('.next');
		const images = galleryWrapper.querySelectorAll('img');
		let currentIndex = 0;
		let autoScrollInterval;

		function updateGallery() {
			galleryWrapper.style.transform = `translateX(-${currentIndex * 100}%)`;
		}

		function startAutoScroll() {
			autoScrollInterval = setInterval(() => {
				currentIndex = (currentIndex < images.length - 1) ? currentIndex + 1 : 0;
				updateGallery();
			}, 5000); // 5 seconds interval
		}

		function stopAutoScroll() {
			clearInterval(autoScrollInterval);
		}

		if (prevButton && nextButton) {
			prevButton.addEventListener('click', () => {
				currentIndex = (currentIndex > 0) ? currentIndex - 1 : images.length - 1;
				updateGallery();
			});

			nextButton.addEventListener('click', () => {
				currentIndex = (currentIndex < images.length - 1) ? currentIndex + 1 : 0;
				updateGallery();
			});
		}

		galleryContainer.addEventListener('mouseenter', stopAutoScroll);
		galleryContainer.addEventListener('mouseleave', startAutoScroll);

		startAutoScroll();
	}
});