// app.js
// Small, dependency-free script:
// - toggles mobile nav visibility (aria-friendly)
// - accessible keyboard handling (Escape closes mobile nav)

/* Utility: select single element */
const $ = (sel) => document.querySelector(sel);
/* Utility: select all */
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

document.addEventListener('DOMContentLoaded', () => {
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

