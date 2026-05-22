// app.js
// Small, dependency-free script:
// - toggles mobile nav visibility (aria-friendly)
// - toggles English <-> Traditional Chinese content
// - preserves language selection in localStorage
// - accessible keyboard handling (Escape closes mobile nav)

/* Utility: select single element */
const $ = (sel) => document.querySelector(sel);
/* Utility: select all */
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

document.addEventListener('DOMContentLoaded', () => {
	// Elements
	const navToggle = $('#nav-toggle');
	const primaryNav = $('#primary-navigation');
	const translateBtn = $('#translate-btn');
	const i18nNodes = $$('[data-i18n]');

	// Translation dictionary (English + Traditional Chinese)
	const translations = {
		en: {
			'nav.home': 'Home',
			'nav.about': 'About Us',
			'nav.classes': 'Classes & Schedule',
			'nav.splendid': 'Splendid China',
			'nav.contact': 'Contact',
			'hero.title': 'Madison Chinese Dance Academy',
			'hero.tagline': 'Connecting community through classical & contemporary Chinese dance.',
			'cta.purchase': 'Purchase Tickets',
			'cta.donate': 'Donate',
			'about.title': 'About Us',
			'about.content': 'Madison Chinese Dance Academy is a community-driven nonprofit offering classes and public performances.',
			'classes.title': 'Classes & Schedule',
			'classes.content': 'We offer beginner to advanced classes for all ages — view our full schedule online.',
			'splendid.title': 'Splendid China',
			'splendid.content': 'Our annual performance showcases traditional and contemporary works.',
			'contact.title': 'Contact',
			'contact.content': 'Email: info@madisonchinesedance.org • Madison, WI',
			'footer.copy': '© 2026 Madison Chinese Dance Academy',
			'footer.contact': 'Community organization — Contact: info@madisonchinesedance.org',
			'translate.btn': '繁體中文'
		},
		zh: {
			'nav.home': '首頁',
			'nav.about': '關於我們',
			'nav.classes': '課程與時程',
			'nav.splendid': '精彩中國演出',
			'nav.contact': '聯絡我們',
			'hero.title': '麥迪遜中華舞蹈學院',
			'hero.tagline': '透過古典與當代中國舞，連結社群。',
			'cta.purchase': '購票',
			'cta.donate': '捐款',
			'about.title': '關於我們',
			'about.content': '麥迪遜中華舞蹈學院為社區非營利組織，提供課程與演出機會。',
			'classes.title': '課程與時程',
			'classes.content': '我們為所有年齡提供初級至高級課程，詳細時程請查閱線上資訊。',
			'splendid.title': '精彩中國演出',
			'splendid.content': '年度演出呈現傳統與當代舞作。',
			'contact.title': '聯絡我們',
			'contact.content': '電子郵件：info@madisonchinesedance.org • 威斯康辛 麥迪遜',
			'footer.copy': '© 2026 麥迪遜中華舞蹈學院',
			'footer.contact': '社區組織 — 聯絡: info@madisonchinesedance.org',
			'translate.btn': 'English'
		}
	};

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

	// I18N: apply language to all nodes with data-i18n key
	function applyLanguage(lang) {
		const dict = translations[lang] || translations.en;
		i18nNodes.forEach(node => {
			const key = node.getAttribute('data-i18n');
			if (!key) return;
			const text = dict[key];
			if (text !== undefined) {
				// Use textContent (safe, avoids HTML injection)
				node.textContent = text;
			}
		});

		// update document language attribute for accessibility / screen readers
		document.documentElement.lang = (lang === 'zh') ? 'zh-Hant' : 'en';

		// update translate button state (label and aria-pressed)
		if (translateBtn) {
			translateBtn.textContent = dict['translate.btn'] || translateBtn.textContent;
			translateBtn.setAttribute('aria-pressed', String(lang === 'zh'));
		}
	}

	// Initialize language from localStorage (persist user's choice)
	const savedLang = localStorage.getItem('mcd_lang') || 'en';
	let currentLang = (savedLang === 'zh') ? 'zh' : 'en';
	applyLanguage(currentLang);

	// Language toggle handler
	if (translateBtn) {
		translateBtn.addEventListener('click', () => {
			currentLang = (currentLang === 'en') ? 'zh' : 'en';
			applyLanguage(currentLang);
			localStorage.setItem('mcd_lang', currentLang);
			// Announce change to assistive tech by updating aria-live (optional)
			// Simple UX: focus the translate button so screen readers pick up its new label
			translateBtn.focus();
		});
	}
});

