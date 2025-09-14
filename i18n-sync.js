const fs = require("fs");
const path = require("path");

// Paths
const localesDir = path.join(__dirname, "locales"); // your JSON translations
const rootDir = __dirname; // scan the project root

// Read all JSON language files
const localeFiles = fs.readdirSync(localesDir).filter(f => f.endsWith(".json"));
const locales = localeFiles.reduce((acc, file) => {
    acc[file] = JSON.parse(fs.readFileSync(path.join(localesDir, file), "utf8"));
    return acc;
}, {});

// Recursive folder walker
const walkDir = dir =>
    fs.readdirSync(dir, { withFileTypes: true }).flatMap(f =>
        f.isDirectory() ? walkDir(path.join(dir, f.name)) : path.join(dir, f.name)
    );

// Scan root folder for .js and .html files
const codeFiles = walkDir(rootDir).filter(f => f.endsWith(".js") || f.endsWith(".html"));

// Collect all translation keys
const allKeys = new Set();
codeFiles.forEach(file => {
    const content = fs.readFileSync(file, "utf8");
    const regex = /t\(["'](.+?)["']\)/g;
    let match;
    while ((match = regex.exec(content)) !== null) {
        allKeys.add(match[1]);
    }
});

// Update locale JSONs
Object.entries(locales).forEach(([file, data]) => {
    let updated = false;
    allKeys.forEach(key => {
        if (!(key in data)) {
            data[key] = file.startsWith("en") ? key : ""; // English filled, others empty
            updated = true;
        }
    });
    if (updated) {
        fs.writeFileSync(path.join(localesDir, file), JSON.stringify(data, null, 2));
        console.log(`${file} updated with new keys`);
    }
});
