const fs = require('fs');
const path = require('path');

const rootDir = path.resolve(__dirname, '..');
const galleryDir = path.join(rootDir, 'images', 'gallery');
const galleryJsonPath = path.join(rootDir, 'content', 'gallery.json');
const imageExtensions = new Set(['.avif', '.gif', '.jpeg', '.jpg', '.png', '.webp']);

function titleFromName(name) {
	return name
		.replace(/\.[^.]+$/, '')
		.replace(/[-_]+/g, ' ')
		.replace(/\s+/g, ' ')
		.trim()
		.replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function relativeUrl(filePath) {
	return path.relative(rootDir, filePath).replace(/\\/g, '/').split('/').map(encodeURIComponent).join('/');
}

function listDirectories(dir) {
	if (!fs.existsSync(dir)) return [];
	return fs.readdirSync(dir, { withFileTypes: true })
		.filter((entry) => entry.isDirectory())
		.map((entry) => entry.name)
		.sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
}

function listImages(dir) {
	if (!fs.existsSync(dir)) return [];
	return fs.readdirSync(dir, { withFileTypes: true })
		.filter((entry) => entry.isFile() && imageExtensions.has(path.extname(entry.name).toLowerCase()))
		.map((entry) => path.join(dir, entry.name))
		.sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
}

function scanGallery() {
	const groups = [];
	const years = listDirectories(galleryDir);

	years.forEach((year) => {
		const yearDir = path.join(galleryDir, year);
		const events = listDirectories(yearDir);
		const yearGroups = [];

		events.forEach((eventName) => {
			const eventDir = path.join(yearDir, eventName);
			const images = listImages(eventDir).map((filePath) => ({
				src: relativeUrl(filePath),
				alt: `${eventName} - ${titleFromName(path.basename(filePath))}`
			}));

			if (images.length > 0) {
				yearGroups.push({
					event: eventName,
					images
				});
			}
		});

		if (yearGroups.length > 0) {
			groups.push({
				year,
				events: yearGroups
			});
		}
	});

	return groups.sort((a, b) => Number(b.year) - Number(a.year));
}

const existing = fs.existsSync(galleryJsonPath)
	? JSON.parse(fs.readFileSync(galleryJsonPath, 'utf8'))
	: {};
const galleryGroups = scanGallery();
const galleryImages = galleryGroups.flatMap((group) => group.events.flatMap((event) => event.images));
const next = {
	...existing,
	galleryGroups,
	galleryImages
};

fs.writeFileSync(galleryJsonPath, `${JSON.stringify(next, null, 2)}\n`);
console.log(`Updated content/gallery.json with ${galleryImages.length} image(s) in ${galleryGroups.length} year group(s).`);
