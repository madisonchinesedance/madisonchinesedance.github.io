const fs = require('fs');
const path = require('path');

const repoRoot = path.resolve(__dirname, '..');
const galleryDir = path.join(repoRoot, 'images', 'gallery');
const contentPath = path.join(repoRoot, 'content', 'gallery.json');
const imageExtensions = new Set(['.avif', '.gif', '.jpeg', '.jpg', '.png', '.webp']);

function titleFromFilename(filename) {
	const basename = path.basename(filename, path.extname(filename));
	return basename
		.replace(/[_-]+/g, ' ')
		.replace(/\s+/g, ' ')
		.trim()
		.replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function readGalleryImages() {
	if (!fs.existsSync(galleryDir)) {
		return [];
	}

	return fs.readdirSync(galleryDir, { withFileTypes: true })
		.filter((entry) => entry.isFile() && imageExtensions.has(path.extname(entry.name).toLowerCase()))
		.sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' }))
		.map((entry) => ({
			src: `../../images/gallery/${entry.name}`,
			thumb: `../../images/gallery/${entry.name}`,
			alt: titleFromFilename(entry.name)
		}));
}

const existingContent = fs.existsSync(contentPath)
	? JSON.parse(fs.readFileSync(contentPath, 'utf8'))
	: {};

const galleryImages = readGalleryImages();
const content = {
	galleryPageTitle: existingContent.galleryPageTitle || 'Gallery | Madison Chinese Dance Academy',
	galleryMetaDescription: existingContent.galleryMetaDescription || 'Image gallery of the Madison Chinese Dance Academy.',
	galleryHeroHeading: existingContent.galleryHeroHeading || 'Gallery',
	galleryGroups: [],
	galleryImages
};

fs.writeFileSync(contentPath, `${JSON.stringify(content, null, 2)}\n`);

console.log(`Updated content/gallery.json with ${galleryImages.length} gallery image${galleryImages.length === 1 ? '' : 's'}.`);
