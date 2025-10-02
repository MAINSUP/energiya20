const fs = require("fs");
const path = require("path");

const localesDir = path.join(__dirname, "locales");
const distDir = path.join(__dirname, "dist");

// Load translations
const translations = {
    en: require(path.join(localesDir, "en.json")),
    uk: require(path.join(localesDir, "uk.json"))
};

// Read template
const template = fs.readFileSync(path.join(__dirname, "src/template.html"), "utf8");

// Replace keys function
function applyTranslations(html, dict) {
    return html.replace(/data-key="([^"]+)">(.*?)</g, (match, key, oldText) => {
        const t = dict[key] || oldText;
        return `data-key="${key}">${t}<`;
    });
}

// Generate pages
for (const [lang, dict] of Object.entries(translations)) {
    let page = applyTranslations(template, dict);
    page = page.replace(/<html lang="en">/, `<html lang="${lang}">`);

    const targetDir = path.join(distDir, lang === "en" ? "" : lang);
    fs.mkdirSync(targetDir, { recursive: true });
    fs.writeFileSync(path.join(targetDir, "index.html"), page, "utf8");
    console.log(`Generated: ${lang}/index.html`);
}
