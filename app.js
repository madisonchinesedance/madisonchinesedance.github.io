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

function getRootPath() {
	const path = window.location.pathname;
	if (!path.includes('/pages/')) {
		return '';
	}

	const pagePath = getPageId();
	const depth = pagePath.split('/').length;
	return '../'.repeat(depth);
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

function defaultHeaderContent(content = {}) {
	const splendidYears = ['2026', '2025', '2024', '2023', '2022', '2021', '2020'];

	return {
		logo: {
			text: content.logoText || 'Madison Chinese Dance Academy',
			shortText: 'MCDA',
			href: 'index.html',
			ariaLabel: `${content.logoText || 'Madison Chinese Dance Academy'} home`
		},
		navigationLabel: 'Primary navigation',
		menuToggleOpenLabel: 'Open navigation',
		menuToggleCloseLabel: 'Close navigation',
		navItems: [
			{ href: 'index.html', page: 'index.html', label: content.navHome || 'Home' },
			{
				label: content.navAbout || 'About Us',
				items: [
					{ href: 'pages/about/about.html', page: 'about/about.html', label: content.navAbout || 'About Us' },
					{ href: 'pages/about/contact.html', page: 'about/contact.html', label: content.navContact || 'Contact' }
				]
			},
			{
				label: 'Community',
				items: [
					{ href: 'pages/community/events.html', page: 'community/events.html', label: 'Events' },
					{ href: 'pages/classes/services.html', page: 'classes/services.html', label: 'Services' }
				]
			},
			{
				label: 'Programs',
				items: [
					{ href: 'pages/classes/dance-classes.html', page: 'classes/dance-classes.html', label: 'Dance Classes' }
				]
			},
			{ href: 'pages/community/gallery.html', page: 'community/gallery.html', label: 'Gallery' },
			{
				label: content.navSplendid || 'Splendid China',
				items: splendidYears.map((year) => ({
					href: `pages/splendid-china/splendid-china-${year}.html`,
					page: `splendid-china/splendid-china-${year}.html`,
					label: `Splendid China ${year}`
				}))
			}
		],
		actions: [
			{
				label: content.ctaTickets || 'Purchase Tickets',
				href: content.ctaTicketsHref || 'pages/tickets.html',
				page: 'tickets.html',
				style: 'primary',
				ariaLabel: content.ctaTickets || 'Purchase Tickets'
			},
			{
				label: content.ctaDonate || 'Donate',
				href: content.ctaDonateHref || 'pages/donate.html',
				page: 'donate.html',
				style: 'secondary',
				ariaLabel: content.ctaDonate || 'Donate'
			}
		]
	};
}

function headerContent(content = {}) {
	const fallback = defaultHeaderContent(content);
	const header = content.header || {};

	return {
		...fallback,
		...header,
		logo: { ...fallback.logo, ...(header.logo || {}) },
		navItems: Array.isArray(header.navItems) ? header.navItems : fallback.navItems,
		actions: Array.isArray(header.actions) ? header.actions : fallback.actions
	};
}

document.addEventListener('DOMContentLoaded', async () => {
	const basePath = getRootPath();
	const currentPage = getPageId();
	const pageContentFile = document.body.getAttribute('data-content-file');
	const [siteContent, pageContent] = await Promise.all([
		loadJson(`${basePath}content/site.json`),
		pageContentFile ? loadJson(`${basePath}content/${pageContentFile}.json`) : Promise.resolve({})
	]);
	const content = { ...siteContent, ...pageContent };
	const header = headerContent(content);

	function resolveHref(href = '') {
		if (!href) return '#';
		if (/^(https?:|mailto:|tel:|#|\/)/.test(href)) return href;
		return `${basePath}${href}`;
	}

	function isActivePage(item) {
		return item.page && currentPage === item.page;
	}

	function navLink(item) {
		const isActive = isActivePage(item);
		const activeClass = isActive ? ' active' : '';
		const currentAttr = isActive ? ' aria-current="page"' : '';
		return `<li class="nav-item"><a href="${resolveHref(item.href)}" class="nav-link${activeClass}"${currentAttr}>${escapeHtml(item.label)}</a></li>`;
	}

	function navMenu(item, index) {
		if (!item.items) return navLink(item);

		const isActive = item.items.some(isActivePage);
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

	function headerAction(action) {
		const isActive = isActivePage(action);
		const currentAttr = isActive ? ' aria-current="page"' : '';
		const style = action.style === 'secondary' ? 'secondary' : 'primary';
		const label = action.label || '';
		const ariaLabel = action.ariaLabel || label;

		return `<a href="${resolveHref(action.href)}" class="btn btn-${style} header-cta" role="button" aria-label="${escapeHtml(ariaLabel)}"${currentAttr}>${escapeHtml(label)}</a>`;
	}

	function renderHeader() {
		const mount = $('[data-site-header]');
		if (!mount) return;

		const logo = header.logo || {};
		const logoText = logo.text || 'Madison Chinese Dance Academy';
		const logoShortText = logo.shortText || 'MCDA';
		const logoAriaLabel = logo.ariaLabel || `${logoText} home`;
		const menuOpenLabel = header.menuToggleOpenLabel || 'Open navigation';
		const actionButtons = header.actions.map(headerAction).join('');

		mount.outerHTML = `
			<header class="site-header" role="banner">
				<div class="container header-inner">
					<div class="header-left">
						<a href="${resolveHref(logo.href || 'index.html')}" class="logo" aria-label="${escapeHtml(logoAriaLabel)}">
							<span class="logo-full-text">${escapeHtml(logoText)}</span>
							<span class="logo-short-text">${escapeHtml(logoShortText)}</span>
						</a>
					</div>

					<nav id="primary-navigation" class="primary-nav" aria-label="${escapeHtml(header.navigationLabel || 'Primary navigation')}">
						<ul class="nav-list">
							${header.navItems.map(navMenu).join('')}
							<li class="nav-cta-list">
								${actionButtons}
							</li>
						</ul>
					</nav>

					<div class="header-controls">
						<button id="nav-toggle" class="nav-toggle" aria-controls="primary-navigation" aria-expanded="false" aria-label="${escapeHtml(menuOpenLabel)}">
							<svg width="24" height="18" viewBox="0 0 24 18" aria-hidden="true" focusable="false">
								<rect width="24" height="2" y="0" rx="1"></rect>
								<rect width="24" height="2" y="8" rx="1"></rect>
								<rect width="24" height="2" y="16" rx="1"></rect>
							</svg>
						</button>
					</div>

					<div class="header-ctas">
						${actionButtons}
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
			navToggle.setAttribute('aria-label', expanded ? header.menuToggleOpenLabel : header.menuToggleCloseLabel);
		});

		// Close mobile nav when any nav link is clicked (improves UX on small screens)
		$$('.nav-link').forEach(link => {
			link.addEventListener('click', () => {
				if (link.classList.contains('nav-menu-toggle')) return;

				if (primaryNav.classList.contains('open')) {
					primaryNav.classList.remove('open');
					navToggle.setAttribute('aria-expanded', 'false');
					navToggle.setAttribute('aria-label', header.menuToggleOpenLabel);
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
				navToggle.setAttribute('aria-label', header.menuToggleOpenLabel);
				navToggle.focus();
			}
		});
	}

	const galleryContainer = $('.gallery-container');
	if (galleryContainer) {
		const galleryWrapper = galleryContainer.querySelector('.gallery-wrapper');
		const galleryGrid = $('[data-gallery-grid]');
		const lightbox = $('[data-gallery-lightbox]');
		const lightboxImage = $('[data-gallery-lightbox-image]');
		const lightboxClose = $('.gallery-lightbox-close');
		const prevButton = galleryContainer.querySelector('.prev');
		const nextButton = galleryContainer.querySelector('.next');
		const galleryGroups = Array.isArray(content.galleryGroups) ? content.galleryGroups : [];
		const groupedImages = galleryGroups.flatMap((group) => {
			const events = Array.isArray(group.events) ? group.events : [];
			return events.flatMap((event) => {
				const images = Array.isArray(event.images) ? event.images : [];
				return images.map((image) => ({
					...image,
					year: group.year,
					event: event.event
				}));
			});
		});
		const galleryImages = groupedImages.length > 0
			? groupedImages
			: (Array.isArray(content.galleryImages) ? content.galleryImages : []);

		if (galleryImages.length > 0) {
			galleryWrapper.innerHTML = galleryImages.map((image, index) => `
				<img src="${escapeHtml(image.src)}" alt="${escapeHtml(image.alt || `Gallery image ${index + 1}`)}">
			`).join('');

			if (galleryGrid) {
				let imageIndex = 0;

				if (galleryGroups.length > 0) {
					galleryGrid.innerHTML = galleryGroups.map((group) => {
						const events = Array.isArray(group.events) ? group.events : [];
						const eventMarkup = events.map((event) => {
							const images = Array.isArray(event.images) ? event.images : [];
							const thumbnails = images.map((image) => {
								const index = imageIndex;
								imageIndex += 1;
								return `
									<button class="gallery-thumb" type="button" data-gallery-thumb="${index}" aria-label="Open ${escapeHtml(image.alt || `gallery image ${index + 1}`)}">
										<img src="${escapeHtml(image.thumb || image.src)}" alt="${escapeHtml(image.alt || `Gallery image ${index + 1}`)}">
									</button>
								`;
							}).join('');

							return `
								<section class="gallery-event" aria-label="${escapeHtml(event.event || `Gallery ${group.year}`)}">
									<h3>${escapeHtml(event.event || `Gallery ${group.year}`)}</h3>
									<div class="gallery-event-grid">${thumbnails}</div>
								</section>
							`;
						}).join('');

						return `
							<section class="gallery-year" aria-label="${escapeHtml(`${group.year} gallery images`)}">
								<h2>${escapeHtml(group.year)}</h2>
								${eventMarkup}
							</section>
						`;
					}).join('');
				} else {
					galleryGrid.innerHTML = galleryImages.map((image, index) => `
						<button class="gallery-thumb" type="button" data-gallery-thumb="${index}" aria-label="Open ${escapeHtml(image.alt || `gallery image ${index + 1}`)}">
							<img src="${escapeHtml(image.thumb || image.src)}" alt="${escapeHtml(image.alt || `Gallery image ${index + 1}`)}">
						</button>
					`).join('');
				}
			}
		}

		const images = Array.from(galleryWrapper.querySelectorAll('img'));
		let currentIndex = 0;
		let autoScrollInterval;

		function updateGallery({ focus = false } = {}) {
			const image = images[currentIndex];
			if (!image) return;

			image.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
			if (focus) image.focus({ preventScroll: true });
		}

		function startAutoScroll() {
			if (autoScrollInterval || images.length < 2) return;

			autoScrollInterval = setInterval(() => {
				currentIndex = (currentIndex < images.length - 1) ? currentIndex + 1 : 0;
				updateGallery();
			}, 5000); // 5 seconds interval
		}

		function stopAutoScroll() {
			clearInterval(autoScrollInterval);
			autoScrollInterval = null;
		}

		images.forEach((image, index) => {
			image.setAttribute('tabindex', '-1');
			image.setAttribute('data-gallery-index', String(index));
		});

		if (prevButton && nextButton) {
			prevButton.addEventListener('click', () => {
				stopAutoScroll();
				currentIndex = (currentIndex > 0) ? currentIndex - 1 : images.length - 1;
				updateGallery({ focus: true });
				startAutoScroll();
			});

			nextButton.addEventListener('click', () => {
				stopAutoScroll();
				currentIndex = (currentIndex < images.length - 1) ? currentIndex + 1 : 0;
				updateGallery({ focus: true });
				startAutoScroll();
			});
		}

		galleryWrapper.addEventListener('scroll', () => {
			const wrapperLeft = galleryWrapper.getBoundingClientRect().left;
			const closestImage = images.reduce((closest, image, index) => {
				const distance = Math.abs(image.getBoundingClientRect().left - wrapperLeft);
				return distance < closest.distance ? { distance, index } : closest;
			}, { distance: Infinity, index: currentIndex });

			currentIndex = closestImage.index;
		}, { passive: true });

		function openLightbox(index) {
			const image = images[index];
			if (!lightbox || !lightboxImage || !image) return;

			stopAutoScroll();
			lightboxImage.src = image.currentSrc || image.src;
			lightboxImage.alt = image.alt;
			lightbox.hidden = false;
			lightboxClose?.focus();
		}

		function closeLightbox() {
			if (!lightbox || !lightboxImage) return;

			lightbox.hidden = true;
			lightboxImage.removeAttribute('src');
			startAutoScroll();
		}

		$$('[data-gallery-thumb]').forEach((button) => {
			button.addEventListener('click', () => {
				const index = Number(button.getAttribute('data-gallery-thumb'));
				if (Number.isNaN(index)) return;

				currentIndex = index;
				updateGallery({ focus: true });
				openLightbox(index);
			});
		});

		lightboxClose?.addEventListener('click', closeLightbox);
		lightbox?.addEventListener('click', (event) => {
			if (event.target === lightbox) closeLightbox();
		});
		document.addEventListener('keydown', (event) => {
			if (event.key === 'Escape' && lightbox && !lightbox.hidden) closeLightbox();
		});

		galleryContainer.addEventListener('mouseenter', stopAutoScroll);
		galleryContainer.addEventListener('mouseleave', startAutoScroll);

		startAutoScroll();
	}
});
