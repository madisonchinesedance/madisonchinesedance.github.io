// app.js
// Small, dependency-free script:
// - loads site config, routes, and page copy from JSON
// - renders shared site header and footer
// - toggles mobile nav visibility (aria-friendly)
// - accessible keyboard handling (Escape closes mobile nav)

/* Utility: select single element */
const $ = (sel) => document.querySelector(sel);
/* Utility: select all */
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

const CONTENT_ROOT = '/content/';

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

function sitePath(relativePath = '') {
	if (!relativePath) return '/';
	const normalized = String(relativePath).replace(/^\/+/, '');
	return `/${normalized}`;
}

function resolveLink(value, routes = {}) {
	if (value === undefined || value === null) return '#';
	const text = String(value);

	if (text.startsWith('@')) {
		const route = routes[text.slice(1)];
		return route ? sitePath(route.href) : '#';
	}

	if (/^(https?:|mailto:|tel:|#)/.test(text)) return text;
	if (text.startsWith('/')) return text;
	return sitePath(text);
}

const ALLOWED_INLINE_TAGS = /<\/?(?:b|strong|i|em|br)\b[^>]*>/gi;

function sanitizeInlineHtml(text) {
	const saved = [];
	let safe = String(text).replace(ALLOWED_INLINE_TAGS, (tag) => {
		const id = saved.push(tag.toLowerCase()) - 1;
		return `\uE000${id}\uE001`;
	});
	safe = escapeHtml(safe);
	return safe.replace(/\uE000(\d+)\uE001/g, (_, index) => saved[Number(index)] || '');
}

function usesParagraphWrapper(element) {
	const tag = element.tagName;
	return tag === 'DIV' || tag === 'SECTION' || element.hasAttribute('data-json-multiline');
}

function shouldUsePlainText(element) {
	if (element.hasAttribute('data-json-attr')) return true;
	if (element.hasAttribute('data-json-plain')) return true;
	const tag = element.tagName;
	return tag === 'TITLE' || tag === 'META' || /^H[1-6]$/.test(tag);
}

function renderRichText(value, element) {
	const text = String(value).replace(/\/n/g, '\n').trim();
	if (!text) return '';

	const blocks = text
		.split(/\n{2,}/)
		.map((paragraph) => paragraph.trim())
		.filter(Boolean)
		.map((paragraph) => paragraph
			.split('\n')
			.map((line) => sanitizeInlineHtml(line))
			.join('<br>'));

	if (usesParagraphWrapper(element)) {
		return blocks.map((block) => `<p>${block}</p>`).join('');
	}

	return blocks.join('<br><br>');
}

function applyJsonContent(content, routes) {
	$$('[data-json]').forEach((element) => {
		const key = element.getAttribute('data-json');
		if (!key || content[key] === undefined) return;

		const value = content[key];
		const attr = element.getAttribute('data-json-attr');
		const hrefKey = element.getAttribute('data-json-href');

		if (attr) {
			element.setAttribute(attr, String(value).replace(/\s+/g, ' ').trim());
		} else if (shouldUsePlainText(element)) {
			element.textContent = value;
		} else {
			if (!['A', 'BUTTON'].includes(element.tagName)) {
				element.classList.add('json-body-text');
			}
			element.innerHTML = renderRichText(value, element);
		}

		if (hrefKey && content[hrefKey] !== undefined) {
			element.setAttribute('href', resolveLink(content[hrefKey], routes));
		}
	});
}

function resolveNavEntry(entry, routes) {
	if (entry.route) {
		const route = routes[entry.route];
		if (!route) return null;

		return {
			href: route.href,
			page: route.page,
			label: entry.label || entry.route
		};
	}

	if (entry.items) {
		return {
			label: entry.label,
			items: entry.items.map((item) => resolveNavEntry(item, routes)).filter(Boolean)
		};
	}

	return null;
}

function buildHeader(header = {}, routes = {}) {
	const logoRoute = header.logo?.route ? routes[header.logo.route] : routes.home;
	const logo = {
		text: header.logo?.text || 'Madison Chinese Dance Academy',
		shortText: header.logo?.shortText || 'MCDA',
		ariaLabel: header.logo?.ariaLabel || 'Madison Chinese Dance Academy home',
		href: logoRoute?.href || 'index.html',
		page: logoRoute?.page || 'index.html'
	};

	return {
		logo,
		navigationLabel: header.navigationLabel || 'Primary navigation',
		menuToggleOpenLabel: header.menuToggleOpenLabel || 'Open navigation',
		menuToggleCloseLabel: header.menuToggleCloseLabel || 'Close navigation',
		navItems: (header.nav || []).map((entry) => resolveNavEntry(entry, routes)).filter(Boolean),
		actions: (header.actions || []).map((action) => {
			const route = routes[action.route];
			if (!route) return null;

			return {
				href: route.href,
				page: route.page,
				label: action.label || action.route,
				style: action.style === 'secondary' ? 'secondary' : 'primary',
				ariaLabel: action.ariaLabel || action.label || action.route
			};
		}).filter(Boolean)
	};
}

function resolveFooterLink(link, routes = {}) {
	if (link.route) {
		const route = routes[link.route];
		if (!route) return null;

		return {
			href: route.href,
			page: route.page,
			label: link.label || link.route
		};
	}

	return {
		href: link.href || '',
		page: null,
		label: link.label || link.href || ''
	};
}

function resolveContentLink(link, routes = {}) {
	if (link.route) {
		const route = routes[link.route];
		if (!route) return null;

		return {
			href: route.href,
			label: link.label || link.heading || link.route
		};
	}

	return {
		href: link.href || '#',
		label: link.label || link.heading || link.href || ''
	};
}

function getPageRouteId(site, pageId) {
	const routes = site.routes || {};
	return Object.keys(routes).find((routeId) => routes[routeId].page === pageId) || null;
}

document.addEventListener('DOMContentLoaded', async () => {
	const currentPage = getPageId();
	const site = await loadJson(`${CONTENT_ROOT}site.json`);
	const headerConfig = await loadJson(`${CONTENT_ROOT}header.json`);
	const footerConfig = await loadJson(`${CONTENT_ROOT}footer.json`);
	const pageRouteId = document.body.getAttribute('data-route')
		|| getPageRouteId(site, currentPage);
	const pageContentPath = pageRouteId ? site.routes?.[pageRouteId]?.content : null;
	const pageContent = pageContentPath
		? await loadJson(`${CONTENT_ROOT}${pageContentPath}`)
		: {};

	const routes = site.routes || {};
	const content = { ...pageContent };
	const header = buildHeader(headerConfig, routes);

	function resolveHref(href = '') {
		return resolveLink(href, routes);
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

	function contentAction(action) {
		const link = resolveContentLink(action, routes);
		if (!link) return '';

		const style = action.style === 'secondary' ? 'secondary' : 'primary';
		return `<a href="${resolveHref(link.href)}" class="btn btn-${style}">${escapeHtml(link.label)}</a>`;
	}

	function renderHomePage() {
		const actionMount = $('[data-home-hero-actions]');
		if (actionMount) {
			const actions = Array.isArray(content.heroActions) ? content.heroActions : [];
			actionMount.innerHTML = actions.map(contentAction).join('');
		}

		const statsMount = $('[data-home-stats]');
		if (statsMount) {
			const stats = Array.isArray(content.stats) ? content.stats : [];
			statsMount.innerHTML = stats.map((stat) => `
				<div class="home-stat">
					<strong>${escapeHtml(stat.value || '')}</strong>
					<span>${escapeHtml(stat.label || '')}</span>
				</div>
			`).join('');
		}

		const featureMount = $('[data-home-feature-cards]');
		if (featureMount) {
			const cards = Array.isArray(content.featureCards) ? content.featureCards : [];
			featureMount.innerHTML = cards.map((card, index) => {
				const link = resolveContentLink(card, routes);
				const href = link ? resolveHref(link.href) : '#';
				const label = link?.label || 'Learn more';

				return `
					<a class="home-feature-card" href="${href}" style="--item-index:${index}">
						<span class="home-card-kicker">${String(index + 1).padStart(2, '0')}</span>
						<h3>${escapeHtml(card.heading || '')}</h3>
						<p>${escapeHtml(card.body || '')}</p>
						<span class="home-card-link">${escapeHtml(label)}</span>
					</a>
				`;
			}).join('');
		}

		const pathwaysMount = $('[data-home-pathways]');
		if (pathwaysMount) {
			const pathways = Array.isArray(content.pathways) ? content.pathways : [];
			pathwaysMount.innerHTML = pathways.map((pathway, index) => {
				const link = resolveContentLink(pathway, routes);
				const href = link ? resolveHref(link.href) : '#';
				const label = link?.label || 'Learn more';

				return `
					<a class="home-pathway" href="${href}" style="--item-index:${index}">
						<h3>${escapeHtml(pathway.heading || '')}</h3>
						<p>${escapeHtml(pathway.body || '')}</p>
						<span>${escapeHtml(label)}</span>
					</a>
				`;
			}).join('');
		}
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

		const brand = footerConfig.brand || {};
		const brandRoute = brand.route ? routes[brand.route] : routes.home;
		const brandHref = resolveHref(brandRoute?.href || 'index.html');
		const brandText = brand.text || 'Madison Chinese Dance Academy';
		const brandShortText = brand.shortText || 'MCDA';
		const mission = brand.mission || '';
		const columns = Array.isArray(footerConfig.columns) ? footerConfig.columns : [];
		const columnMarkup = columns.map((column) => {
			const links = Array.isArray(column.links) ? column.links : [];
			const items = links
				.map((link) => resolveFooterLink(link, routes))
				.filter(Boolean)
				.map((link) => {
					if (!link.href) {
						return `<li><span>${escapeHtml(link.label)}</span></li>`;
					}

					return `<li><a href="${resolveHref(link.href)}">${escapeHtml(link.label)}</a></li>`;
				})
				.join('');

			return `
				<section class="footer-column" aria-label="${escapeHtml(column.heading || 'Footer links')}">
					<h2>${escapeHtml(column.heading || 'Links')}</h2>
					<ul>${items}</ul>
				</section>
			`;
		}).join('');

		mount.outerHTML = `
			<footer class="site-footer" role="contentinfo">
				<div class="container footer-inner">
					<section class="footer-brand" aria-label="${escapeHtml(brandText)}">
						<a href="${brandHref}" class="footer-logo" aria-label="${escapeHtml(`${brandText} home`)}">
							<span>${escapeHtml(brandShortText)}</span>
						</a>
						<p class="footer-brand-name">${escapeHtml(brandText)}</p>
						<p class="footer-mission">${escapeHtml(mission)}</p>
					</section>

					<nav class="footer-directory" aria-label="Footer navigation">
						${columnMarkup}
					</nav>
				</div>
				<div class="container footer-bottom">
					<p class="footer-copy">${escapeHtml(footerConfig.copyright || '© 2026 Madison Chinese Dance Academy')}</p>
				</div>
			</footer>
		`;
	}

	applyJsonContent(content, routes);
	renderHomePage();
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
				<img src="${escapeHtml(resolveLink(image.src, routes))}" alt="${escapeHtml(image.alt || `Gallery image ${index + 1}`)}">
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
										<img src="${escapeHtml(resolveLink(image.thumb || image.src, routes))}" alt="${escapeHtml(image.alt || `Gallery image ${index + 1}`)}">
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
							<img src="${escapeHtml(resolveLink(image.thumb || image.src, routes))}" alt="${escapeHtml(image.alt || `Gallery image ${index + 1}`)}">
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
