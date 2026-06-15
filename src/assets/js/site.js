// app.js
// Small, dependency-free script:
// - loads site config, routes, and page copy from JSON
// - renders shared site header and footer
// - toggles mobile nav visibility (aria-friendly)
// - accessible keyboard handling (Escape closes mobile nav)

/* Utility: select single element */
const $ = (sel) => document.querySelector(sel);
/* Simple markdown-to-HTML for chatbot messages.
   Converts **bold**, *italic*, ## headings, --- hr, and paragraphs. */
function markdownToHtml(text) {
	const esc = String(text)
		.replace(/[&]/g, () => '\x26amp;')
		.replace(/[<]/g, () => '\x26lt;')
		.replace(/[>]/g, () => '\x26gt;')
		.replace(/["]/g, () => '\x26quot;');
	const md = esc
		.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
		.replace(/\*(.+?)\*/g, '<em>$1</em>');
	// Split on blank lines for paragraph/block-level yield
	return md.split(/\n{2,}/).map(b => {
		const block = b.trim();
		if (!block) return '';
		if (/^#/.test(block)) {
			const inline = block.replace(/\n/g, ' ');
			if (/^### /.test(inline)) return '<h3>' + inline.slice(4) + '</h3>';
			if (/^## /.test(inline)) return '<h2>' + inline.slice(3) + '</h2>';
			if (/^# /.test(inline)) return '<h1>' + inline.slice(2) + '</h1>';
		}
		if (/^---+$/.test(block)) return '<hr>';
		// Paragraph: replace remaining newlines with spaces
		return '<p>' + block.replace(/\n/g, ' ') + '</p>';
	}).filter(Boolean).join('');
}

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
		.replace(/[&]/g, () => '\x26amp;')
		.replace(/[<]/g, () => '\x26lt;')
		.replace(/[>]/g, () => '\x26gt;')
		.replace(/["]/g, () => '\x26quot;')
		.replace(/[']/g, () => '\x26#39;');
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

function renderRichTextValue(value) {
	const text = String(value || '').replace(/\/n/g, '\n').trim();
	if (!text) return '';

	return text
		.split(/\n{2,}/)
		.map((paragraph) => paragraph.trim())
		.filter(Boolean)
		.map((paragraph) => paragraph
			.split('\n')
			.map((line) => sanitizeInlineHtml(line))
			.join('<br>'))
		.map((block) => `<p>${block}</p>`)
		.join('');
}

function blockId(block, fallback) {
	return block.id ? escapeHtml(block.id) : fallback;
}

function findSectionComponent(sections = [], key) {
	for (const section of sections) {
		for (const item of section?.items || []) {
			const blocks = item?.blocks;
			if (Array.isArray(blocks)) {
				for (const block of blocks) {
					if (block?.type === key) return block;
				}
			}
			for (const [itemKey, value] of Object.entries(item || {})) {
				if (itemKey.replace(/_\d+$/, '') === key) return value;
			}
		}
	}
	return null;
}

function resolveNavEntry(entry, routes) {
	if (entry.route) {
		const route = routes[entry.route];
		if (!route) return null;

		return {
			routeId: entry.route,
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

function buildHeader(header = {}, routes = {}, announcementsConfig = {}) {
	const logoRoute = header.logo?.route ? routes[header.logo.route] : routes.home;
	const logo = {
		text: header.logo?.text || 'Madison Chinese Dance Academy',
		shortText: header.logo?.shortText || 'MCDA',
		ariaLabel: header.logo?.ariaLabel || 'Madison Chinese Dance Academy home',
		href: logoRoute?.href || 'index.html',
		page: logoRoute?.page || 'index.html'
	};
	const highlights = announcementsConfig.highlights || {};

	return {
		logo,
		navigationLabel: header.navigationLabel || 'Primary navigation',
		menuToggleOpenLabel: header.menuToggleOpenLabel || 'Open navigation',
		menuToggleCloseLabel: header.menuToggleCloseLabel || 'Close navigation',
		navItems: (header.nav || []).map((entry) => resolveNavEntry(entry, routes)).filter(Boolean),
		highlights: {
			enabled: highlights.enabled !== false,
			style: highlights.style || 'pulse',
			color: highlights.color || 'peach',
			navRoutes: highlights.navRoutes || [],
			actionRoutes: highlights.actionRoutes || []
		},
		announcements: (announcementsConfig.announcements || []).map((announcement) => {
			if (announcement.enabled === false) return null;

			return {
				id: announcement.id || announcement.label || announcement.body || 'announcement',
				label: announcement.label || '',
				body: announcement.body || '',
				actions: (announcement.actions || []).map((action) => {
					const link = resolveContentLink(action, routes);
					if (!link) return null;

					return {
						routeId: action.route || null,
						href: link.href,
						label: link.label,
						style: 'primary',
						ariaLabel: action.ariaLabel || link.label
					};
				}).filter(Boolean)
			};
		}).filter(Boolean),
		actions: (header.actions || []).map((action) => {
			const route = routes[action.route];
			if (!route) return null;

			return {
				routeId: action.route,
				href: route.href,
				page: route.page,
				label: action.label || action.route,
				style: 'primary',
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

document.addEventListener('DOMContentLoaded', () => {
	const ANNOUNCEMENT_DISMISS_KEY = 'mcda-announcement-dismissed';
	const CHATBOT_MESSAGES_KEY = 'mcda-chatbot-messages';
	const navigationEntry = performance.getEntriesByType?.('navigation')?.[0];
	if (navigationEntry?.type === 'reload') {
		sessionStorage.removeItem(ANNOUNCEMENT_DISMISS_KEY);
		sessionStorage.removeItem(CHATBOT_MESSAGES_KEY);
	}

	const pageRouteId = document.body.getAttribute('data-route') || 'home';
	const header = {
		menuToggleOpenLabel: 'Open navigation',
		menuToggleCloseLabel: 'Close navigation',
	};

	if (sessionStorage.getItem(ANNOUNCEMENT_DISMISS_KEY) === 'true') {
		document.querySelector('.site-announcement')?.remove();
		document.querySelector('.site-header')?.classList.remove('has-visible-announcement');
	}

	function resolveHref(href = '') {
		return resolveLink(href, {});
	}

	function isAnnouncementDismissed() {
		return sessionStorage.getItem(ANNOUNCEMENT_DISMISS_KEY) === 'true';
	}

	function isActivePage(item) {
		return item.page && currentPage === item.page;
	}

	function highlightClass(type, routeId) {
		if (!header.highlights?.enabled || !routeId) return '';
		const targetRoutes = type === 'action'
			? header.highlights.actionRoutes
			: header.highlights.navRoutes;

		if (!targetRoutes.includes(routeId)) return '';
		return ` is-announcement-highlight is-announcement-highlight-${escapeHtml(header.highlights.color)} is-announcement-highlight-${escapeHtml(header.highlights.style)}`;
	}

	function navLink(item) {
		const isActive = isActivePage(item);
		const activeClass = isActive ? ' active' : '';
		const importantClass = highlightClass('nav', item.routeId);
		const currentAttr = isActive ? ' aria-current="page"' : '';
		return `<li class="nav-item"><a href="${resolveHref(item.href)}" class="nav-link${activeClass}${importantClass}"${currentAttr}>${escapeHtml(item.label)}</a></li>`;
	}

	function navMenu(item, index) {
		if (!item.items) return navLink(item);

		const isActive = item.items.some(isActivePage);
		const activeClass = isActive ? ' active' : '';
		const importantClass = item.items.some((child) => highlightClass('nav', child.routeId)) ? highlightClass('nav', item.items.find((child) => highlightClass('nav', child.routeId))?.routeId) : '';
		const menuId = `nav-menu-${index}`;

		return `
			<li class="nav-item nav-item-dropdown">
				<button class="nav-link nav-menu-toggle${activeClass}${importantClass}" type="button" aria-expanded="false" aria-controls="${menuId}">
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
		const style = 'primary';
		const label = action.label || '';
		const ariaLabel = action.ariaLabel || label;
		const importantClass = highlightClass('action', action.routeId);

		return `<a href="${resolveHref(action.href)}" class="btn btn-${style} header-cta${importantClass}" role="button" aria-label="${escapeHtml(ariaLabel)}"${currentAttr}>${escapeHtml(label)}</a>`;
	}

	function contentAction(action) {
		const link = resolveContentLink(action, routes);
		if (!link) return '';

		const style = 'primary';
		const targetAttr = action.newTab ? ' target="_blank" rel="noopener noreferrer"' : '';
		const className = action.className ? ` ${escapeHtml(action.className)}` : '';
		const ariaLabel = action.ariaLabel ? ` aria-label="${escapeHtml(action.ariaLabel)}"` : '';
		return `<a href="${resolveHref(link.href)}" class="btn btn-${style}${className}" role="button"${targetAttr}${ariaLabel}>${escapeHtml(link.label)}</a>`;
	}

	const FONT_SIZE_PRESETS = {
		'heading-1': 'var(--heading-1-font-size)',
		'heading-2': 'var(--heading-2-font-size)',
		'heading-3': 'var(--heading-3-font-size)',
		'heading-4': 'var(--heading-4-font-size)',
		'heading-5': 'var(--heading-5-font-size)',
		'heading-6': 'var(--heading-6-font-size)',
		body: 'var(--body-font-size)',
		lg: 'clamp(1.12rem, 1.4vw, 1.3rem)'
	};

	const CSS_SIZE_PATTERN = /^(?:var\(--[a-z0-9-]+\)|clamp\([^;{}]+\)|min\([^;{}]+\)|max\([^;{}]+\)|calc\([^;{}]+\)|[\d.]+(?:rem|em|px|%|vw|vh))$/i;

	function resolveFontSize(value = '') {
		const token = String(value || '').trim();
		if (!token) return '';
		if (FONT_SIZE_PRESETS[token]) return FONT_SIZE_PRESETS[token];
		return CSS_SIZE_PATTERN.test(token) ? token : '';
	}

	function normalizeAlign(value = '') {
		const align = String(value || '').trim().toLowerCase();
		return ['left', 'center', 'right'].includes(align) ? align : '';
	}

	function resolveHeadingLevel(block = {}, fallback = 2) {
		const token = String(block.fontSize || block.headingSize || '').trim();
		const match = /^heading-([1-6])$/.exec(token);
		if (match) return Number(match[1]);
		if (block.level) return Math.min(Math.max(Number(block.level), 1), 6);
		return Math.min(Math.max(Number(fallback), 1), 6);
	}

	function blockTypographyStyle(block = {}) {
		const parts = [];
		const fontSize = resolveFontSize(block.fontSize || block.headingSize);
		if (fontSize) parts.push(`font-size:${fontSize}`);
		const align = normalizeAlign(block.align);
		if (align && align !== 'left') parts.push(`text-align:${align}`);
		return parts.length ? ` style="${parts.join(';')}"` : '';
	}

	function itemAlignStyle(item = {}) {
		const align = normalizeAlign(item.align);
		return align && align !== 'left' ? `text-align:${align};` : '';
	}

	function resolveSectionClasses(section = {}) {
		return [
			section.name ? `section-${section.name}` : '',
			section.className || ''
		].filter(Boolean).join(' ');
	}

	function resolveItemClasses(item = {}) {
		return item.className || '';
	}

	function normalizeLegacyBlockKey(key = '', value = {}) {
		const baseKey = key.replace(/_\d+$/, '');
		if (/^heading([1-6])$/.test(baseKey)) {
			return { type: 'heading', fontSize: `heading-${baseKey[7]}`, ...value };
		}
		if (/^statistic\d+$/.test(baseKey)) {
			return { type: 'heading', fontSize: 'heading-4', ...value };
		}
		if (baseKey === 'body') {
			return { type: 'body', ...value };
		}
		if (baseKey === 'gallery') {
			return { type: 'gallery', ...value };
		}
		if (baseKey === 'zeffyEmbed') {
			return { type: 'zeffyEmbed', ...value };
		}
		return null;
	}

	function normalizeItem(item = {}) {
		if (Array.isArray(item.blocks)) {
			return item;
		}

		if (!Object.keys(item).some((key) => {
			const baseKey = key.replace(/_\d+$/, '');
			return /^heading[1-6]$/.test(baseKey)
				|| /^statistic\d+$/.test(baseKey)
				|| ['body', 'gallery', 'zeffyEmbed'].includes(baseKey);
		})) {
			const link = resolveContentLink(item, routes);
			const actions = link?.href && link.href !== '#'
				? [{
					href: link.href,
					label: link.label || item.label || 'Learn more',
					newTab: item.newTab
				}]
				: [];

			return {
				...item,
				blocks: [
					{
						type: 'heading',
						text: item.heading || item.value || '',
						id: item.id,
						fontSize: item.headingSize || 'heading-4'
					},
					{
						type: 'body',
						text: item.body || '',
						actions
					}
				]
			};
		}

		const legacyOrder = Object.keys(item).filter((key) => !['name', 'className', 'variant', 'align', 'link', 'route', 'href', 'label', 'newTab', 'heading', 'value', 'body', 'id', 'headingSize'].includes(key));
		const blocks = legacyOrder
			.map((key) => normalizeLegacyBlockKey(key, item[key]))
			.filter(Boolean);

		return { ...item, blocks };
	}

	function renderHeadingBlock(block = {}, level = 2, context = {}) {
		const safeLevel = resolveHeadingLevel(block, level);
		const text = block.text || block.heading || '';
		if (!text) return '';

		const id = blockId(block, '');
		const idAttr = id ? ` id="${id}"` : '';
		const styleAttr = blockTypographyStyle(block);
		const classes = [
			block.className
		].filter(Boolean).map(escapeHtml).join(' ');
		const classAttr = classes ? ` class="${classes}"` : '';

		return `<h${safeLevel}${idAttr}${classAttr}${styleAttr}>${escapeHtml(text)}</h${safeLevel}>`;
	}

	function renderBodyBlock(block = {}, context = {}) {
		const text = block.text || block.body || '';
		const body = renderRichTextValue(text);
		const actions = Array.isArray(block.actions) && block.actions.length
			? `<div class="component-actions">${block.actions.map(contentAction).join('')}</div>`
			: '';
		const styleAttr = blockTypographyStyle(block);
		const classes = [
			'component-body',
			block.className
		].filter(Boolean).map(escapeHtml).join(' ');

		return body || actions ? `<div class="${classes}"${styleAttr}>${body}${actions}</div>` : '';
	}

	function renderGalleryBlock(block = {}) {
		const galleryVariant = String(block.variant || '').trim();
		const variantAttr = galleryVariant ? ` data-gallery-variant="${escapeHtml(galleryVariant)}"` : '';
		const isRunner = /^runner(?:-tall|-wide)?$/.test(galleryVariant);
		const isFeatured = galleryVariant === 'featured';
		const isArchive = galleryVariant === 'archive';
		const carousel = `
			<div class="gallery-container"${variantAttr}>
				<div class="gallery-wrapper" data-gallery-carousel></div>
				<div class="gallery-controls" aria-label="Gallery controls">
					<button class="prev" type="button" aria-label="Previous image">&#10094;</button>
					<button class="next" type="button" aria-label="Next image">&#10095;</button>
				</div>
			</div>
		`;

		if (isFeatured) {
			return `
				<section class="gallery-section gallery-section-featured" aria-label="Featured gallery photos">
					${carousel}
					<div class="gallery-dots" data-gallery-dots aria-label="Featured gallery image selection"></div>
					<div class="gallery-featured-thumbs" data-gallery-featured-thumbs aria-label="Featured gallery thumbnails"></div>
				</section>
			`;
		}

		if (isArchive) {
			return `
				<section class="gallery-section gallery-section-archive" aria-label="Splendid China gallery photos">
					${carousel}
					<div class="gallery-grid" data-gallery-grid aria-label="Gallery image thumbnails"></div>
				</section>
			`;
		}

		if (isRunner) {
			return `
				${carousel}
				<div class="gallery-dots" data-gallery-dots aria-label="Gallery image selection"></div>
			`;
		}

		return `
			${carousel}
			<div class="gallery-grid" data-gallery-grid aria-label="Gallery image thumbnails"></div>
		`;
	}

	function ensureGalleryLightbox() {
		if ($('[data-gallery-lightbox]') || !$('.gallery-container')) return;

		document.body.insertAdjacentHTML('beforeend', `
			<div class="gallery-lightbox" data-gallery-lightbox hidden>
				<div class="gallery-lightbox-window" role="dialog" aria-modal="true" aria-label="Gallery image preview">
					<button class="gallery-lightbox-close" type="button" aria-label="Close gallery image preview">&times;</button>
					<img src="" alt="" data-gallery-lightbox-image>
				</div>
			</div>
		`);
	}

	function renderZeffyEmbedBlock(block = {}) {
		const formUrl = block.formUrl || '';
		const iframeSrc = block.iframeSrc || (formUrl ? `https://www.zeffy.com${formUrl}` : '');
		if (!formUrl && !iframeSrc) return '';

		return `
			<div class="ticket-embed">
				${formUrl ? `<div data-zeffy-embed data-form-url="${escapeHtml(formUrl)}"></div>` : ''}
				<div data-zeffy-embed-fallback>
					<div class="zeffy-fallback-frame">
						<iframe title="${escapeHtml(block.iframeTitle || 'Embedded form powered by Zeffy')}" src="${escapeHtml(iframeSrc)}" allowpaymentrequest allowTransparency="true"></iframe>
					</div>
				</div>
			</div>
		`;
	}

	function renderSectionItem(item = {}, context = {}, index = 0) {
		const normalizedItem = normalizeItem(item);
		const itemBlocks = Array.isArray(normalizedItem.blocks) ? normalizedItem.blocks : [];
		const link = resolveContentLink(normalizedItem, routes);
		const href = link?.href ? resolveHref(link.href) : '';
		const tag = href && href !== '#' ? 'a' : 'article';
		const hrefAttr = tag === 'a' ? ` href="${href}"` : '';
		const itemClass = resolveItemClasses(normalizedItem);
		const className = itemClass ? ` ${escapeHtml(itemClass)}` : '';
		const alignStyle = itemAlignStyle(normalizedItem);
		const styleAttr = `--item-index:${index};${alignStyle}`;

		return `
			<${tag} class="section-item${className}" style="${styleAttr}"${hrefAttr}>
				${renderBlocks(itemBlocks, context)}
			</${tag}>
		`;
	}

	function renderBlock(block = {}, context = {}) {
		if (!block.type) {
			return renderSectionBlock(block);
		}

		if (block.type === 'heading') {
			return renderHeadingBlock(block, 2, context);
		}

		const builders = {
			heading1: () => renderHeadingBlock(block, 1, context),
			heading2: () => renderHeadingBlock(block, 2, context),
			body: () => renderBodyBlock(block, context),
			gallery: () => renderGalleryBlock(block),
			zeffyEmbed: () => renderZeffyEmbedBlock(block)
		};

		const builder = builders[block.type];
		return builder ? builder() : '';
	}

	function renderBlocks(blocks = [], context = {}) {
		return blocks.map((block) => renderBlock(block, context)).join('');
	}

	function findSectionHeadingId(items = []) {
		for (const item of items) {
			if (Array.isArray(item)) {
				const nestedId = findSectionHeadingId(item);
				if (nestedId) return nestedId;
				continue;
			}
			const normalized = normalizeItem(item);
			const heading = (normalized.blocks || []).find((entry) => entry.type === 'heading' && entry.id);
			if (heading?.id) return heading.id;
		}
		return '';
	}

	function renderSectionBlock(block = {}) {
		const items = Array.isArray(block.items) ? block.items : [];
		const columns = Math.max(1, Math.min(Number(block.columns || items.length || 1), 4));
		const classes = [
			'section',
			'page-section',
			columns > 1 ? 'section-columns' : '',
			resolveSectionClasses(block)
		]
			.filter(Boolean)
			.map(escapeHtml)
			.join(' ');
		const headingId = findSectionHeadingId(items);
		const labelledBy = headingId ? ` aria-labelledby="${escapeHtml(headingId)}"` : '';

		return `
			<section class="${classes}"${labelledBy}>
				<div class="container">
					<div class="section-grid" style="--section-columns:${columns}">
						${items.map((item, index) => Array.isArray(item)
							? `<article class="section-item" style="--item-index:${index};">${renderBlocks(item)}</article>`
							: renderSectionItem(item, {}, index)
						).join('')}
					</div>
				</div>
			</section>
		`;
	}

	function renderPageBlocks() {
		const mount = $('[data-page-blocks]') || $('.site-main');
		if (!mount) return;

		const sections = Array.isArray(content.sections) ? content.sections : [];
		if (!sections.length) return;
		mount.innerHTML = renderBlocks(sections);
	}

	function loadZeffyEmbedScript() {
		if (!$('[data-zeffy-embed]')) return;
		if ($('script[data-zeffy-embed-script]')) return;

		const script = document.createElement('script');
		script.src = 'https://www.zeffy.com/embed/v2/zeffy-embed.js';
		script.defer = true;
		script.setAttribute('data-zeffy-embed-script', '');
		script.onerror = () => {
			$$('[data-zeffy-embed-fallback]').forEach((element) => {
				element.style.display = 'block';
			});
		};
		document.body.appendChild(script);
	}

	function shuffle(items) {
		const list = items.slice();
		for (let i = list.length - 1; i > 0; i -= 1) {
			const j = Math.floor(Math.random() * (i + 1));
			[list[i], list[j]] = [list[j], list[i]];
		}
		return list;
	}

	function createNebulaLayer(blobCount = 7) {
		const palette = shuffle([
			'rgba(77, 212, 232, 0.45)',
			'rgba(94, 184, 212, 0.42)',
			'rgba(216, 93, 75, 0.40)',
			'rgba(107, 91, 218, 0.38)',
			'rgba(90, 50, 180, 0.38)',
			'rgba(232, 184, 109, 0.30)',
			'rgba(184, 111, 212, 0.35)',
		]).slice(0, blobCount);

		const blobs = palette.map((color) => {
			const x = (Math.random() * 88 + 6).toFixed(1);
			const y = (Math.random() * 88 + 6).toFixed(1);
			const w = (Math.random() * 28 + 28).toFixed(1);
			const h = (Math.random() * 22 + 22).toFixed(1);
			const opacity = (Math.random() * 0.18 + 0.52).toFixed(2);

			return `<span class="site-nebula" style="--nebula-x:${x}%;--nebula-y:${y}%;--nebula-w:${w}%;--nebula-h:${h}%;--nebula-color:${color};--nebula-opacity:${opacity};"></span>`;
		}).join('');

		return `<div class="page-nebula-layer" aria-hidden="true">${blobs}</div>`;
	}

	function createStarField(className, count = 120, yMax = 100) {
		const starTints = [
			'var(--color-violet)',
			'var(--color-sunrise)',
			'#c98fd4',
			'#7eb8cc',
		];

		const stars = Array.from({ length: count }, () => {
			const size = (Math.random() * 3.5 + 2).toFixed(2);
			const opacity = (Math.random() * 0.3 + 0.65).toFixed(2);
			const x = (Math.random() * 100).toFixed(2);
			const y = (Math.random() * yMax).toFixed(2);
			const duration = (Math.random() * 2.8 + 2.2).toFixed(2);
			const delay = (Math.random() * -5).toFixed(2);
			const drift = (Math.random() * 14 - 7).toFixed(2);
			const tint = Math.random() < 0.12
				? `--star-tint:${starTints[Math.floor(Math.random() * starTints.length)]};`
				: '';

			return `<span class="site-star" style="--star-x:${x}%; --star-y:${y}%; --star-size:${size}px; --star-opacity:${opacity}; --star-duration:${duration}s; --star-delay:${delay}s; --star-drift:${drift}px; ${tint}"></span>`;
		}).join('');

		return `<div class="${className}" aria-hidden="true">${createNebulaLayer()}${stars}</div>`;
	}

	function renderPageStars() {
		const main = $('.site-main');
		if (!main) return;

		main.querySelector('.page-star-field')?.remove();
		main.insertAdjacentHTML('afterbegin', createStarField('page-star-field', 150));
	}

	function renderChatbot() {
		document.body.insertAdjacentHTML('beforeend', `
			<div class="chatbot" id="chatbot" role="region" aria-label="Chat assistant">
				<button class="chatbot-toggle" id="chatbot-toggle" type="button" aria-expanded="false" aria-controls="chatbot-panel" aria-label="Open chat assistant">
					<svg class="chatbot-icon" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
						<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
					</svg>
					<svg class="chatbot-icon-close" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
						<line x1="18" y1="6" x2="6" y2="18"></line>
						<line x1="6" y1="6" x2="18" y2="18"></line>
					</svg>
					<span class="chatbot-toggle-label">MCDA ASSISTANT</span>
				</button>

				<div class="chatbot-panel" id="chatbot-panel" role="dialog" aria-modal="true" aria-label="Chat assistant" hidden>
					<div class="chatbot-header">
						<div class="chatbot-header-info">
							<div class="chatbot-avatar" aria-hidden="true">
								<span class="chatbot-logo">MCDA</span>
							</div>
							<div>
								<h3 class="chatbot-title">MCDA ASSISTANT</h3>
								<span class="chatbot-status">BETA</span>
							</div>
						</div>
						<div class="chatbot-header-actions">
							<button class="chatbot-clear" id="chatbot-clear" type="button" aria-label="Clear chat">
								<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
									<polyline points="3 6 5 6 21 6"></polyline>
									<path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
								</svg>
							</button>
							<button class="chatbot-minimize" id="chatbot-minimize" type="button" aria-label="Minimize chat">
								<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
									<line x1="5" y1="12" x2="19" y2="12"></line>
								</svg>
							</button>
						</div>
					</div>

					<div class="chatbot-messages" id="chatbot-messages" role="log" aria-live="polite" aria-label="Conversation">
						<div class="chatbot-message bot">
							<div class="chatbot-message-avatar" aria-hidden="true">
								<span class="chatbot-logo">MCDA</span>
							</div>
							<div class="chatbot-message-content">
								<p>Hello! I'm the MCDA Assistant. How can I help you today?</p>
							</div>
						</div>
						<div class="chatbot-message bot chatbot-notice">
							<div class="chatbot-message-avatar" aria-hidden="true">
								<span class="chatbot-logo">MCDA</span>
							</div>
							<div class="chatbot-message-content">
								<p><strong>Note:</strong> This chatbot is in testing stage and may not work properly. For urgent inquiries, please contact the academy directly.</p>
							</div>
						</div>
					</div>

					<div class="chatbot-suggestions" id="chatbot-suggestions"></div>
					<div class="chatbot-input-area">
						<form class="chatbot-form" id="chatbot-form">
							<input
								type="text"
								class="chatbot-input"
								id="chatbot-input"
								placeholder="Type your message..."
								autocomplete="off"
								aria-label="Chat message"
								required
							>
							<button type="submit" class="chatbot-send" id="chatbot-send" aria-label="Send message">
								<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
									<line x1="22" y1="2" x2="11" y2="13"></line>
									<polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
								</svg>
							</button>
						</form>
						<p class="chatbot-disclaimer">AI assistant. Responses may not be accurate.</p>
					</div>
				</div>
			</div>
		`);
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
		const hasVisibleAnnouncements = !isAnnouncementDismissed() && header.announcements.length > 0;
		const announcementMarkup = !hasVisibleAnnouncements ? '' : header.announcements.map((announcement) => {
			const actions = announcement.actions.map((action) => `
				<a class="announcement-btn announcement-btn-${escapeHtml(action.style)}" href="${resolveHref(action.href)}" aria-label="${escapeHtml(action.ariaLabel)}">
					${escapeHtml(action.label)}
				</a>
			`).join('');

			return `
				<section class="site-announcement" data-announcement-id="${escapeHtml(announcement.id)}" aria-label="${escapeHtml(announcement.label || 'Site announcement')}">
					<div class="container announcement-inner">
						<div class="announcement-copy">
							${announcement.label ? `<span class="announcement-label">${escapeHtml(announcement.label)}</span>` : ''}
							${announcement.body ? `<span class="announcement-body">${escapeHtml(announcement.body)}</span>` : ''}
						</div>
						<div class="announcement-actions">
							${actions}
							<button class="announcement-dismiss" type="button" aria-label="Dismiss announcement" title="Dismiss">
								<span aria-hidden="true">&times;</span>
							</button>
						</div>
					</div>
				</section>
			`;
		}).join('');

		mount.outerHTML = `
			<header class="site-header${hasVisibleAnnouncements ? ' has-visible-announcement' : ''}" role="banner">
				<div class="container header-inner">
					<div class="header-left">
					<a href="${resolveHref(logo.href || 'index.html')}" class="logo" aria-label="${escapeHtml(logoAriaLabel)}">
							<span class="logo-icon" aria-hidden="true">
								<svg width="32" height="32" viewBox="0 0 32 32" fill="none">
									<circle cx="16" cy="16" r="14.5" stroke="currentColor" stroke-width="1.5"/>
									<text x="16" y="14" text-anchor="middle" fill="currentColor" font-size="9" font-weight="800" font-family="inherit" letter-spacing="0.5">MC</text>
									<text x="16" y="24" text-anchor="middle" fill="currentColor" font-size="9" font-weight="800" font-family="inherit" letter-spacing="0.5">DA</text>
								</svg>
							</span>
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
							<svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
								<rect width="24" height="2" y="3" rx="1"></rect>
								<rect width="24" height="2" y="11" rx="1"></rect>
								<rect width="24" height="2" y="19" rx="1"></rect>
							</svg>
						</button>
					</div>

					<div class="header-ctas">
						${actionButtons}
					</div>
				</div>
				${announcementMarkup}
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

		const operations = Array.isArray(footerConfig.operations) ? footerConfig.operations : [];
		const operationsMarkup = operations.map((op) => {
			if (!op.href) {
				return `<span>${escapeHtml(op.label)}</span>`;
			}
			const href = op.href.startsWith('mailto:') || op.href.startsWith('tel:') ? op.href : resolveHref(op.href);
			return `<a href="${escapeHtml(href)}">${escapeHtml(op.label)}</a>`;
		}).join('<br>');

		mount.outerHTML = `
			<footer class="site-footer" role="contentinfo">
				<div class="container footer-inner">
					<section class="footer-brand" aria-label="${escapeHtml(brandText)}">
					<a href="${brandHref}" class="footer-logo" aria-label="${escapeHtml(`${brandText} home`)}">
							<span class="footer-logo-icon" aria-hidden="true">
								<svg width="40" height="40" viewBox="0 0 32 32" fill="none">
									<circle cx="16" cy="16" r="14.5" stroke="currentColor" stroke-width="1.5"/>
									<text x="16" y="14" text-anchor="middle" fill="currentColor" font-size="9" font-weight="800" font-family="inherit" letter-spacing="0.5">MC</text>
									<text x="16" y="24" text-anchor="middle" fill="currentColor" font-size="9" font-weight="800" font-family="inherit" letter-spacing="0.5">DA</text>
								</svg>
							</span>
						</a>
						<p class="footer-brand-name">${escapeHtml(brandText)}</p>
						<p class="footer-mission">${escapeHtml(mission)}</p>
						${operationsMarkup ? `<div class="footer-operations">${operationsMarkup}</div>` : ''}
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

	loadZeffyEmbedScript();
	renderPageStars();

	// Elements
	const announcementDismiss = $('.announcement-dismiss');
	const navToggle = $('#nav-toggle');
	const primaryNav = $('#primary-navigation');
	const dropdownToggles = $$('.nav-menu-toggle');

	// If announcement text overflows, convert to scrolling (marquee) layout.
	// Only the body text scrolls — the label stays fixed.
	function enableAnnouncementScroll(announcementSection) {
		const copy = announcementSection.querySelector('.announcement-copy');
		if (!copy) return;

		const body = copy.querySelector('.announcement-body');
		if (!body) return;

		// Check if the body text overflows the available width
		const container = announcementSection.querySelector('.announcement-inner');
		if (!container) return;

		const actionsEl = announcementSection.querySelector('.announcement-actions');
		const actionsWidth = actionsEl ? actionsEl.offsetWidth + 12 : 0; // 12 = gap
		const label = copy.querySelector('.announcement-label');
		const labelWidth = label ? label.offsetWidth + 8 : 0; // 8 = gap
		const availableWidth = container.offsetWidth - actionsWidth - labelWidth - 24; // 24 = padding/gap
		const textWidth = body.scrollWidth;

		if (textWidth > availableWidth) {
			announcementSection.classList.add('has-scroll-text');

			// Create a scroll-track inside the body span with duplicated content
			const track = document.createElement('span');
			track.className = 'announcement-scroll-track';

			const item1 = document.createElement('span');
			item1.className = 'announcement-scroll-item';
			item1.textContent = body.textContent;

			const item2 = document.createElement('span');
			item2.className = 'announcement-scroll-item';
			item2.textContent = body.textContent;

			track.appendChild(item1);
			track.appendChild(item2);

			// Replace the body's text content with the scroll track
			body.innerHTML = '';
			body.appendChild(track);
		}
	}

	if (announcementDismiss) {
		announcementDismiss.addEventListener('click', () => {
			sessionStorage.setItem(ANNOUNCEMENT_DISMISS_KEY, 'true');
			announcementDismiss.closest('.site-announcement')?.remove();
			$('.site-header')?.classList.remove('has-visible-announcement');
		});
	}

	// Activate announcement scrolling if text overflows
	const announcementSection = $('.site-announcement');
	if (announcementSection) {
		enableAnnouncementScroll(announcementSection);
	}

	function closeDropdowns(exceptToggle = null) {
		dropdownToggles.forEach((toggle) => {
			if (toggle === exceptToggle) return;
			toggle.setAttribute('aria-expanded', 'false');
			toggle.closest('.nav-item-dropdown')?.classList.remove('open');
		});
	}

	function updateNavCollapse() {
		const siteHeader = $('.site-header');
		const headerInner = $('.header-inner');
		if (!siteHeader || !headerInner) return;

		siteHeader.classList.remove('is-nav-collapsed');
		const overflows = headerInner.scrollWidth > headerInner.clientWidth + 1;
		const shouldCollapse = overflows || window.matchMedia('(max-width: 992px)').matches;
		siteHeader.classList.toggle('is-nav-collapsed', shouldCollapse);

		if (!shouldCollapse && primaryNav?.classList.contains('open')) {
			primaryNav.classList.remove('open');
			navToggle?.setAttribute('aria-expanded', 'false');
			navToggle?.setAttribute('aria-label', header.menuToggleOpenLabel || 'Open navigation');
			closeDropdowns();
		}
	}

	updateNavCollapse();

	let navCollapseResizeTimer;
	window.addEventListener('resize', () => {
		clearTimeout(navCollapseResizeTimer);
		navCollapseResizeTimer = setTimeout(updateNavCollapse, 100);
	});

	const headerInner = $('.header-inner');
	if (headerInner && typeof ResizeObserver !== 'undefined') {
		const navCollapseObserver = new ResizeObserver(() => updateNavCollapse());
		navCollapseObserver.observe(headerInner);
	}

	if (document.fonts?.ready) {
		document.fonts.ready.then(updateNavCollapse);
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

	const lightbox = $('[data-gallery-lightbox]');
	const lightboxImage = $('[data-gallery-lightbox-image]');
	const lightboxClose = $('.gallery-lightbox-close');
	let activeGalleryRunner = null;

	function initGalleryRunner({
		galleryContainer,
		galleryDots = null,
		galleryGrid = null,
		featuredThumbs = null,
		galleryGroups = [],
		galleryBlock = {},
		useYearTabs = false,
		getFallbackImages = () => [],
	}) {
		if (!galleryContainer) return null;

		const galleryWrapper = galleryContainer.querySelector('.gallery-wrapper');
		if (!galleryWrapper) return null;

		const useDots = !!galleryDots;
		const prevButton = galleryContainer.querySelector('.prev');
		const nextButton = galleryContainer.querySelector('.next');
		const groupedImages = galleryGroups.flatMap((group) => {
			const events = Array.isArray(group.events) ? group.events : [];
			return events.flatMap((event) => {
				const eventImages = Array.isArray(event.images) ? event.images : [];
				return eventImages.map((image) => ({
					...image,
					year: group.year,
					event: event.event
				}));
			});
		});
		let activeYearIndex = 0;
		let images = [];
		let currentIndex = 0;
		let autoScrollInterval;

		function imagesForActiveYear() {
			if (!useYearTabs) {
				return groupedImages.length > 0
					? groupedImages
					: (Array.isArray(galleryBlock.images)
						? galleryBlock.images
						: getFallbackImages());
			}
			const activeGroup = galleryGroups[activeYearIndex];
			if (!activeGroup) return [];
			const events = Array.isArray(activeGroup.events) ? activeGroup.events : [];
			return events.flatMap((event) => {
				const eventImages = Array.isArray(event.images) ? event.images : [];
				return eventImages.map((image) => ({
					...image,
					year: activeGroup.year,
					event: event.event
				}));
			});
		}

		function renderYearTabs() {
			if (!useYearTabs) return;
			const tabHost = galleryContainer.parentElement;
			if (tabHost?.querySelector('.gallery-year-tabs')) return;

			const tabs = document.createElement('div');
			tabs.className = 'gallery-year-tabs';
			tabs.setAttribute('role', 'tablist');
			tabs.setAttribute('aria-label', 'Filter gallery by year');
			tabs.innerHTML = galleryGroups.map((group, index) => {
				const year = group.year || `Group ${index + 1}`;
				const isActive = index === activeYearIndex;
				const totalImages = (group.events || []).reduce((sum, event) => {
					return sum + (Array.isArray(event.images) ? event.images.length : 0);
				}, 0);
				return `
					<button class="gallery-year-tab${isActive ? ' active' : ''}" type="button" role="tab" data-gallery-year-tab="${index}" aria-selected="${isActive}" tabindex="${isActive ? '0' : '-1'}">
						<span class="gallery-year-tab-label">${escapeHtml(year)}</span>
						<span class="gallery-year-tab-count" aria-hidden="true">${totalImages}</span>
					</button>
				`;
			}).join('');
			tabHost?.insertBefore(tabs, galleryContainer);
		}

		function updateSelectionIndicators() {
			if (useDots && galleryDots) {
				galleryDots.querySelectorAll('.gallery-dot').forEach((dot) => {
					const dotIndex = Number(dot.getAttribute('data-gallery-dot'));
					dot.classList.toggle('active', dotIndex === currentIndex);
				});
			}
			if (featuredThumbs) {
				featuredThumbs.querySelectorAll('.gallery-thumb').forEach((thumb) => {
					const thumbIndex = Number(thumb.getAttribute('data-gallery-thumb'));
					thumb.classList.toggle('active', thumbIndex === currentIndex);
				});
			}
		}

		function renderYear() {
			const preRendered = galleryWrapper.querySelectorAll('img').length > 0;
			if (preRendered && !useYearTabs) {
				images = Array.from(galleryWrapper.querySelectorAll('img'));
				if (useDots && galleryDots) {
					galleryDots.innerHTML = images.map((image, index) => `
						<button class="gallery-dot ${index === 0 ? 'active' : ''}" type="button" data-gallery-dot="${index}" aria-label="Go to image ${index + 1}"></button>
					`).join('');
				}
				if (featuredThumbs) {
					featuredThumbs.innerHTML = images.map((image, index) => `
						<button class="gallery-thumb${index === 0 ? ' active' : ''}" type="button" data-gallery-thumb="${index}" aria-label="Open ${escapeHtml(image.alt || `gallery image ${index + 1}`)}">
							<img src="${escapeHtml(image.currentSrc || image.src)}" alt="${escapeHtml(image.alt || `Gallery image ${index + 1}`)}" loading="lazy" decoding="async">
						</button>
					`).join('');
				}
				images.forEach((image, index) => {
					image.setAttribute('tabindex', '-1');
					image.setAttribute('data-gallery-index', String(index));
					image.style.cursor = 'pointer';
					image.addEventListener('click', () => {
						stopAutoScroll();
						currentIndex = index;
						openLightbox(index);
					});
				});
				currentIndex = 0;
				updateSelectionIndicators();
				return;
			}

			const activeImages = imagesForActiveYear();

			if (activeImages.length > 0) {
				galleryWrapper.innerHTML = activeImages.map((image, index) => `
					<img src="${escapeHtml(image.src)}" alt="${escapeHtml(image.alt || `Gallery image ${index + 1}`)}">
				`).join('');

				if (useDots && galleryDots) {
					galleryDots.innerHTML = activeImages.map((image, index) => `
						<button class="gallery-dot ${index === 0 ? 'active' : ''}" type="button" data-gallery-dot="${index}" aria-label="Go to image ${index + 1}"></button>
					`).join('');
				} else if (galleryGrid) {
					if (useYearTabs) {
						const activeGroup = galleryGroups[activeYearIndex];
						const events = Array.isArray(activeGroup?.events) ? activeGroup.events : [];
						let thumbIndex = 0;
						const eventMarkup = events.map((event) => {
							const eventImages = Array.isArray(event.images) ? event.images : [];
							const thumbnails = eventImages.map((image) => {
								const localIndex = thumbIndex;
								thumbIndex += 1;
								return `
									<button class="gallery-thumb" type="button" data-gallery-thumb="${localIndex}" aria-label="Open ${escapeHtml(image.alt || `gallery image ${localIndex + 1}`)}">
										<img src="${escapeHtml(image.thumb || image.src)}" alt="${escapeHtml(image.alt || `Gallery image ${localIndex + 1}`)}" loading="lazy" decoding="async">
									</button>
								`;
							}).join('');
							if (!thumbnails) return '';
							return `
								<section class="gallery-event" aria-label="${escapeHtml(event.event || `Gallery ${activeGroup?.year || ''}`)}">
									<h3>${escapeHtml(event.event || `Gallery ${activeGroup?.year || ''}`)}</h3>
									<div class="gallery-event-grid">${thumbnails}</div>
								</section>
							`;
						}).join('');
						galleryGrid.innerHTML = eventMarkup || '<p class="gallery-empty-message">No images are available for this year.</p>';
					} else if (galleryGroups.length > 0) {
						let imageIndex = 0;
						galleryGrid.innerHTML = galleryGroups.map((group) => {
							const events = Array.isArray(group.events) ? group.events : [];
							const eventMarkup = events.map((event) => {
								const groupImages = Array.isArray(event.images) ? event.images : [];
								const thumbnails = groupImages.map((image) => {
									const index = imageIndex;
									imageIndex += 1;
									return `
										<button class="gallery-thumb" type="button" data-gallery-thumb="${index}" aria-label="Open ${escapeHtml(image.alt || `gallery image ${index + 1}`)}">
										<img src="${escapeHtml(image.thumb || image.src)}" alt="${escapeHtml(image.alt || `Gallery image ${index + 1}`)}" loading="lazy">
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
						galleryGrid.innerHTML = activeImages.map((image, index) => `
							<button class="gallery-thumb" type="button" data-gallery-thumb="${index}" aria-label="Open ${escapeHtml(image.alt || `gallery image ${index + 1}`)}">
								<img src="${escapeHtml(image.thumb || image.src)}" alt="${escapeHtml(image.alt || `Gallery image ${index + 1}`)}" loading="lazy">
							</button>
						`).join('');
					}
				}

				if (featuredThumbs) {
					featuredThumbs.innerHTML = activeImages.map((image, index) => `
						<button class="gallery-thumb${index === 0 ? ' active' : ''}" type="button" data-gallery-thumb="${index}" aria-label="Open ${escapeHtml(image.alt || `gallery image ${index + 1}`)}">
							<img src="${escapeHtml(image.thumb || image.src)}" alt="${escapeHtml(image.alt || `Gallery image ${index + 1}`)}" loading="lazy" decoding="async">
						</button>
					`).join('');
				}
			} else {
				galleryWrapper.innerHTML = '<div class="gallery-empty-message" role="status">No images to display.</div>';
				if (galleryGrid) {
					galleryGrid.innerHTML = '<p class="gallery-empty-message">No images are available for this gallery.</p>';
				}
				if (galleryDots) {
					galleryDots.innerHTML = '';
				}
				if (featuredThumbs) {
					featuredThumbs.innerHTML = '';
				}
			}

			images = Array.from(galleryWrapper.querySelectorAll('img'));
			images.forEach((image, index) => {
				image.setAttribute('tabindex', '-1');
				image.setAttribute('data-gallery-index', String(index));
				image.style.cursor = 'pointer';
				image.addEventListener('click', () => {
					stopAutoScroll();
					currentIndex = index;
					openLightbox(index);
				});
			});
			currentIndex = 0;
			updateSelectionIndicators();
		}

		function updateGallery({ focus = false, scroll = true, behavior = 'smooth' } = {}) {
			const image = images[currentIndex];
			if (!image) return;

			if (scroll) {
				galleryWrapper.scrollTo({
					left: currentIndex * galleryWrapper.clientWidth,
					behavior,
				});
			}
			if (focus) image.focus({ preventScroll: true });

			updateSelectionIndicators();
		}

		function startAutoScroll() {
			if (autoScrollInterval || images.length < 2) return;

			autoScrollInterval = setInterval(() => {
				currentIndex = (currentIndex < images.length - 1) ? currentIndex + 1 : 0;
				updateGallery({ scroll: true });
			}, 5000);
		}

		function stopAutoScroll() {
			clearInterval(autoScrollInterval);
			autoScrollInterval = null;
		}

		function openLightbox(index) {
			const image = images[index];
			if (!lightbox || !lightboxImage || !image) return;

			activeGalleryRunner = runner;
			stopAutoScroll();
			lightboxImage.src = image.currentSrc || image.src;
			lightboxImage.alt = image.alt;
			lightbox.hidden = false;
			lightboxClose?.focus();
		}

		const runner = { startAutoScroll, stopAutoScroll };

		renderYearTabs();
		renderYear();

		if (useYearTabs) {
			const tabHost = galleryContainer.parentElement;
			tabHost?.querySelectorAll('.gallery-year-tab').forEach((tab) => {
				tab.addEventListener('click', () => {
					const index = Number(tab.getAttribute('data-gallery-year-tab'));
					if (Number.isNaN(index) || index === activeYearIndex) return;

					stopAutoScroll();
					activeYearIndex = index;
					tabHost.querySelectorAll('.gallery-year-tab').forEach((yearTab) => {
						const isActive = Number(yearTab.getAttribute('data-gallery-year-tab')) === activeYearIndex;
						yearTab.classList.toggle('active', isActive);
						yearTab.setAttribute('aria-selected', String(isActive));
						yearTab.setAttribute('tabindex', isActive ? '0' : '-1');
					});
					renderYear();
					startAutoScroll();
				});
			});
		}

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
			updateSelectionIndicators();
		}, { passive: true });

		if (galleryGrid) {
			galleryGrid.addEventListener('click', (event) => {
				const button = event.target.closest('[data-gallery-thumb]');
				if (!button) return;
				const index = Number(button.getAttribute('data-gallery-thumb'));
				if (Number.isNaN(index)) return;

				stopAutoScroll();
				currentIndex = index;
				openLightbox(index);
			});
		}

		if (galleryDots) {
			galleryDots.addEventListener('click', (event) => {
				const button = event.target.closest('[data-gallery-dot]');
				if (!button) return;
				const index = Number(button.getAttribute('data-gallery-dot'));
				if (Number.isNaN(index)) return;

				stopAutoScroll();
				currentIndex = index;
				updateGallery({ focus: true });
				startAutoScroll();
			});
		}

		if (featuredThumbs) {
			featuredThumbs.addEventListener('click', (event) => {
				const button = event.target.closest('[data-gallery-thumb]');
				if (!button) return;
				const index = Number(button.getAttribute('data-gallery-thumb'));
				if (Number.isNaN(index)) return;

				stopAutoScroll();
				currentIndex = index;
				updateGallery({ focus: true });
				openLightbox(index);
			});
		}

		galleryContainer.addEventListener('mouseenter', stopAutoScroll);
		galleryContainer.addEventListener('mouseleave', startAutoScroll);

		startAutoScroll();
		return runner;
	}

	const galleryRunners = [];

	document.querySelectorAll('.gallery-container').forEach((galleryContainer) => {
		if (galleryContainer.dataset.galleryInitialized === 'true') return;

		const variant = galleryContainer.getAttribute('data-gallery-variant') || '';
		const galleryHost = galleryContainer.closest('.gallery-section') || galleryContainer.parentElement;
		const galleryDots = galleryHost?.querySelector('[data-gallery-dots]') || null;
		const galleryGrid = galleryHost?.querySelector('[data-gallery-grid]') || null;
		const featuredThumbs = galleryHost?.querySelector('[data-gallery-featured-thumbs]') || null;

		let fallbackImages = [];
		try {
			fallbackImages = JSON.parse(galleryContainer.getAttribute('data-gallery-images') || '[]');
		} catch (error) {
			fallbackImages = [];
		}

		let galleryGroups = [];
		const groupsHost = galleryContainer.closest('[data-gallery-groups]');
		if (groupsHost) {
			try {
				galleryGroups = JSON.parse(groupsHost.getAttribute('data-gallery-groups') || '[]');
			} catch (error) {
				galleryGroups = [];
			}
		}

		if (variant === 'featured' && fallbackImages.length === 0) {
			galleryHost.hidden = true;
			return;
		}

		const isArchive = variant === 'archive';
		const isRunner = /^runner(?:-tall|-wide)?$/.test(variant);
		const runner = initGalleryRunner({
			galleryContainer,
			galleryDots,
			galleryGrid,
			featuredThumbs,
			galleryGroups: isArchive ? galleryGroups : [],
			galleryBlock: {},
			useYearTabs: isArchive && galleryGroups.length > 1,
			getFallbackImages: () => fallbackImages,
		});

		if (runner) {
			galleryContainer.dataset.galleryInitialized = 'true';
			galleryRunners.push(runner);
		} else if (isRunner) {
			galleryContainer.dataset.galleryInitialized = 'true';
		}
	});

	if (lightbox) {
		lightboxClose?.addEventListener('click', () => {
			if (!lightboxImage) return;
			lightbox.hidden = true;
			lightboxImage.removeAttribute('src');
			activeGalleryRunner?.startAutoScroll();
			activeGalleryRunner = null;
		});
		lightbox.addEventListener('click', (event) => {
			if (event.target !== lightbox) return;
			lightbox.hidden = true;
			lightboxImage?.removeAttribute('src');
			activeGalleryRunner?.startAutoScroll();
			activeGalleryRunner = null;
		});
		document.addEventListener('keydown', (event) => {
			if (event.key === 'Escape' && !lightbox.hidden) {
				lightbox.hidden = true;
				lightboxImage?.removeAttribute('src');
				activeGalleryRunner?.startAutoScroll();
				activeGalleryRunner = null;
			}
		});
	}

	// Chatbot functionality
	const chatbot = $('#chatbot');
	const chatbotToggle = $('#chatbot-toggle');
	const chatbotPanel = $('#chatbot-panel');
	const chatbotMinimize = $('#chatbot-minimize');
	const chatbotForm = $('#chatbot-form');
	const chatbotInput = $('#chatbot-input');
	const chatbotMessages = $('#chatbot-messages');
		const chatbotSend = $('#chatbot-send');
		const chatbotClear = $('#chatbot-clear');
	const chatbotSuggestions = $('#chatbot-suggestions');

	// Page-specific suggested prompts
	const SUGGESTED_PROMPTS = {
		home: [
			'What programs do you offer?',
			'How can I get involved?',
			'When is the next performance?'
		],
		about: [
			'What is the mission of MCDA?',
			'Who leads the academy?',
			'How can I contact MCDA?'
		],
		'beginner-dancers': [
			'When do classes start?',
			'How do I register for classes?',
			'What should I wear to class?'
		],
		'intermediate-dancers': [
			'What level is intermediate?',
			'How do I prepare for intermediate classes?',
			'Can I move up to advanced?'
		],
		'advanced-dancers': [
			'What does the advanced program involve?',
			'Are there performance opportunities?',
			'How do I audition?'
		],
		'dance-with-us': [
			'What classes are available for adults?',
			'Do I need experience to join?',
			'What is the class schedule?'
		],
		'book-a-performance': [
			'How do I book a performance?',
			'What types of performances do you offer?',
			'What is the pricing for a booking?'
		],
		'see-a-performance': [
			'When is the next show?',
			'Where are performances held?',
			'How do I buy tickets?'
		],
		'support-our-cause': [
			'How can I donate?',
			'Are donations tax-deductible?',
			'What does my donation support?'
		],
		donate: [
			'How do I make a donation?',
			'What payment methods are accepted?',
			'Can I set up recurring donations?'
		],
		tickets: [
			'How do I purchase tickets?',
			'Are there group discounts?',
			'What is the refund policy?'
		],
		events: [
			'What upcoming events are planned?',
			'How do I RSVP for an event?',
			'Can I volunteer at events?'
		],
		services: [
			'What community services do you provide?',
			'How can I request a cultural workshop?',
			'Do you offer virtual programs?'
		],
		faq: [
			'What is the class schedule?',
			'What is your refund policy?',
			'Do you offer private lessons?'
		],
		gallery: [
			'How can I appear in the gallery?',
			'Can I submit my photos?',
			'How do I view past performances?'
		]
	};

		if (chatbot && chatbotToggle && chatbotPanel) {
		// Load saved chat messages from sessionStorage
		// Render page-specific suggestion bubbles
		function renderSuggestions() {
			if (!chatbotSuggestions) return;
			const routeId = pageRouteId || 'home';
			const prompts = SUGGESTED_PROMPTS[routeId] || SUGGESTED_PROMPTS.home;
			chatbotSuggestions.innerHTML = prompts.map((prompt) =>
				`<button type="button" class="chatbot-suggestion-btn">${escapeHtml(prompt)}</button>`
			).join('');
		}

		// Handle suggestion clicks
		function setupSuggestionClicks() {
			if (!chatbotSuggestions) return;
			chatbotSuggestions.addEventListener('click', (e) => {
				const btn = e.target.closest('.chatbot-suggestion-btn');
				if (!btn) return;
				e.stopPropagation();
				const text = btn.textContent;
				chatbotSuggestions.innerHTML = '';
				sendMessage(text);
			});
		}

		// Hide suggestions after first interaction
		function hideSuggestions() {
			if (chatbotSuggestions) {
				chatbotSuggestions.innerHTML = '';
			}
		}

		function loadSavedMessages() {
			try {
				const saved = sessionStorage.getItem(CHATBOT_MESSAGES_KEY);
				if (!saved) return false;
				const messages = JSON.parse(saved);
				if (!Array.isArray(messages) || messages.length === 0) return false;

				// Clear the default welcome messages
				chatbotMessages.innerHTML = '';

				// Re-render each saved message
				messages.forEach(({ text, isUser }) => {
					const messageDiv = document.createElement('div');
					messageDiv.className = `chatbot-message ${isUser ? 'user' : 'bot'}`;

					const avatarDiv = document.createElement('div');
					avatarDiv.className = 'chatbot-message-avatar';
					avatarDiv.setAttribute('aria-hidden', 'true');
					avatarDiv.innerHTML = isUser
						? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>'
						: '<span class="chatbot-logo">MCDA</span>';

					const contentDiv = document.createElement('div');
					contentDiv.className = 'chatbot-message-content';
					if (isUser) {
						const p = document.createElement('p');
						p.textContent = text;
						contentDiv.appendChild(p);
					} else {
						contentDiv.dataset.rawText = text;
						contentDiv.innerHTML = markdownToHtml(text);
					}

					messageDiv.appendChild(avatarDiv);
					messageDiv.appendChild(contentDiv);
					chatbotMessages.appendChild(messageDiv);
				});

				chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
				return true;
			} catch (e) {
				return false;
			}
		}

		// Save chat messages to sessionStorage
		function saveMessages() {
			try {
				const messages = [];
				chatbotMessages.querySelectorAll('.chatbot-message').forEach((msg) => {
					const contentEl = msg.querySelector('.chatbot-message-content');
					if (contentEl) {
						// For user messages, use the p tag's textContent; for bot messages use rawText
						const text = msg.classList.contains('user')
							? (contentEl.querySelector('p')?.textContent || '')
							: (contentEl.dataset.rawText || '');
						messages.push({ text, isUser: msg.classList.contains('user') });
					}
				});
				sessionStorage.setItem(CHATBOT_MESSAGES_KEY, JSON.stringify(messages));
			} catch (e) {
				// Silently fail if sessionStorage is unavailable
			}
		}

		// Render suggestions only if no saved messages exist
		if (!loadSavedMessages()) {
			renderSuggestions();
			setupSuggestionClicks();
		}

		// Clear chat button
		if (chatbotClear) {
			chatbotClear.addEventListener('click', () => {
				chatbotMessages.innerHTML = '';
				const welcomeMsg = document.createElement('div');
				welcomeMsg.className = 'chatbot-message bot';
				welcomeMsg.innerHTML = `
					<div class="chatbot-message-avatar" aria-hidden="true"><span class="chatbot-logo">MCDA</span></div>
					<div class="chatbot-message-content"><p>Chat cleared. How can I help you?</p></div>
				`;
				chatbotMessages.appendChild(welcomeMsg);
				chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
				sessionStorage.removeItem(CHATBOT_MESSAGES_KEY);
			});
		}

		function toggleChatbot() {
			const isOpen = chatbotToggle.getAttribute('aria-expanded') === 'true';
			chatbotToggle.setAttribute('aria-expanded', String(!isOpen));
			chatbotPanel.hidden = isOpen;
			if (!isOpen) {
				chatbotInput.focus();
			}
		}

		chatbotToggle.addEventListener('click', toggleChatbot);

		if (chatbotMinimize) {
			chatbotMinimize.addEventListener('click', toggleChatbot);
		}

		// Close chatbot on Escape key
		document.addEventListener('keydown', (e) => {
			if (e.key === 'Escape' && chatbotToggle.getAttribute('aria-expanded') === 'true') {
				toggleChatbot();
				chatbotToggle.focus();
			}
		});

		// Close chatbot when clicking outside
		document.addEventListener('click', (e) => {
			if (chatbotToggle.getAttribute('aria-expanded') === 'true' &&
				!chatbot.contains(e.target)) {
				toggleChatbot();
			}
		});

		function addMessage(text, isUser = false) {
			const messageDiv = document.createElement('div');
			messageDiv.className = `chatbot-message ${isUser ? 'user' : 'bot'}`;

			const avatarDiv = document.createElement('div');
			avatarDiv.className = 'chatbot-message-avatar';
			avatarDiv.setAttribute('aria-hidden', 'true');
			avatarDiv.innerHTML = isUser
				? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>'
				: '<span class="chatbot-logo">MCDA</span>';

			const contentDiv = document.createElement('div');
			contentDiv.className = 'chatbot-message-content';
			if (isUser) {
				const p = document.createElement('p');
				p.textContent = text;
				contentDiv.appendChild(p);
			} else {
				contentDiv.dataset.rawText = text;
				contentDiv.innerHTML = markdownToHtml(text);
			}

			messageDiv.appendChild(avatarDiv);
			messageDiv.appendChild(contentDiv);

			chatbotMessages.appendChild(messageDiv);
			chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
			saveMessages();
		}

		function showTypingIndicator() {
			const typingDiv = document.createElement('div');
			typingDiv.className = 'chatbot-message bot chatbot-typing';
			typingDiv.innerHTML = `
				<div class="chatbot-message-avatar" aria-hidden="true">
					<span class="chatbot-logo">MCDA</span>
				</div>
				<div class="chatbot-message-content">
					<div class="chatbot-typing-dots">
						<span></span><span></span><span></span>
					</div>
				</div>
			`;
			chatbotMessages.appendChild(typingDiv);
			chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
			return typingDiv;
		}

		function removeTypingIndicator(typingDiv) {
			typingDiv.remove();
		}

		// Cloudflare Worker endpoint (deploy your worker and update this URL)
		// The worker will call Cloudflare Workers AI with your API key stored securely
		const CHATBOT_API_ENDPOINT = 'https://mcda-ai-bot.joshuacheng-dev.workers.dev/'; // UPDATE THIS

		async function sendMessage(message) {
			// Add user message
			addMessage(message, true);
			chatbotInput.value = '';
			chatbotSend.disabled = true;

			// Show typing indicator
			const typingIndicator = showTypingIndicator();

			try {
				const response = await fetch(CHATBOT_API_ENDPOINT, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ message })
				});

				if (!response.ok) {
					throw new Error(`HTTP error! status: ${response.status}`);
				}

				const data = await response.json();
				const botResponse = data.response || 'Sorry, I could not process your request.';

				removeTypingIndicator(typingIndicator);
				addMessage(botResponse, false);
			} catch (error) {
				removeTypingIndicator(typingIndicator);
				addMessage('Sorry, there was an error processing your request. Please try again.', false);
				console.error('Chatbot error:', error);
			} finally {
				chatbotSend.disabled = false;
				chatbotInput.focus();
			}
		}

		if (chatbotForm) {
			chatbotForm.addEventListener('submit', (e) => {
				e.preventDefault();
				const message = chatbotInput.value.trim();
				if (message) {
					sendMessage(message);
				}
			});
		}
	}
});

/* -------------------------------------------------
   CSS for typing indicator (injected via JS to keep
   all chatbot styles together, but you can move this
   to style.css if preferred)
   ------------------------------------------------- */
const chatbotStyles = `
<style>
.chatbot-typing .chatbot-message-content {
	background: linear-gradient(180deg, var(--color-violet), var(--color-deep-navy));
	border: 1px solid var(--edge-contrast);
	border-radius: 16px;
	border-bottom-left-radius: 4px;
	padding: 12px 16px;
}
.chatbot-typing-dots {
	display: flex;
	gap: 4px;
}
.chatbot-typing-dots span {
	width: 8px;
	height: 8px;
	border-radius: 50%;
	background: var(--light-text-color);
	opacity: 0.5;
	animation: chatbot-typing-bounce 1.4s ease-in-out infinite both;
}
.chatbot-typing-dots span:nth-child(1) { animation-delay: -0.32s; }
.chatbot-typing-dots span:nth-child(2) { animation-delay: -0.16s; }
@keyframes chatbot-typing-bounce {
	0%, 80%, 100% { transform: scale(0); opacity: 0.5; }
	40% { transform: scale(1); opacity: 1; }
}
</style>
`;
document.head.insertAdjacentHTML('beforeend', chatbotStyles);
