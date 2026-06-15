const markdownIt = require("markdown-it");

const md = markdownIt({
  html: true,
  breaks: true,
  linkify: true,
});

module.exports = function (eleventyConfig) {
  eleventyConfig.addPassthroughCopy("src/assets");
  eleventyConfig.addPassthroughCopy("CNAME");
  eleventyConfig.addPassthroughCopy("src/.nojekyll");

  eleventyConfig.addFilter("markdown", (value) => {
    if (!value) return "";
    return md.render(String(value));
  });

  eleventyConfig.addFilter("escapeHtml", (value) => {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  });

  eleventyConfig.addFilter("isActive", (href, pageUrl) => {
    if (!href || !pageUrl) return false;
    const normalize = (url) => {
      if (!url || url === "/") return "/index.html";
      return url.endsWith("/") ? `${url}index.html` : url;
    };
    return normalize(href) === normalize(pageUrl);
  });

  eleventyConfig.addFilter("highlightNav", (href, announcements) => {
    const highlights = announcements?.highlights;
    if (!highlights?.enabled) return "";
    const routes = highlights.navRoutes || [];
    const hrefToRoute = {
      "/index.html": "home",
      "/pages/gallery.html": "gallery",
      "/pages/programs.html": "programs",
      "/pages/tickets.html": "tickets",
      "/pages/donate.html": "donate",
    };
    for (const [path, routeId] of Object.entries(hrefToRoute)) {
      if (href === path && routes.includes(routeId)) {
        return ` is-announcement-highlight is-announcement-highlight-${highlights.color || "gold"} is-announcement-highlight-${highlights.style || "pulse"}`;
      }
    }
    if (href?.includes("/splendid-china/")) {
      const year = href.match(/splendid-china-(\d{4})/)?.[1];
      if (year && routes.includes(`splendid-china-${year}`)) {
        return ` is-announcement-highlight is-announcement-highlight-${highlights.color || "gold"} is-announcement-highlight-${highlights.style || "pulse"}`;
      }
    }
    return "";
  });

  eleventyConfig.addFilter("highlightAction", (href, announcements) => {
    const highlights = announcements?.highlights;
    if (!highlights?.enabled) return "";
    const routes = highlights.actionRoutes || [];
    if (href === "/pages/tickets.html" && routes.includes("tickets")) {
      return ` is-announcement-highlight is-announcement-highlight-${highlights.color || "gold"} is-announcement-highlight-${highlights.style || "pulse"}`;
    }
    if (href === "/pages/donate.html" && routes.includes("donate")) {
      return ` is-announcement-highlight is-announcement-highlight-${highlights.color || "gold"} is-announcement-highlight-${highlights.style || "pulse"}`;
    }
    return "";
  });

  eleventyConfig.addFilter("json", (value) => JSON.stringify(value ?? null));

  return {
    dir: {
      input: "src",
      output: "_site",
      includes: "_includes",
      data: "_data",
    },
    htmlTemplateEngine: "njk",
    markdownTemplateEngine: "njk",
    templateFormats: ["md", "njk", "html"],
  };
};
