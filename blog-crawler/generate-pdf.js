import puppeteer from 'puppeteer';
import { PDFDocument } from 'pdf-lib';
import fs from 'fs/promises';
import { execSync } from 'child_process'; // for running Ghostscript

// --- CONFIGURATION ---
const BASE_URL = 'http://localhost:4321'; 
const OUTPUT_FILE = 'adam-korga-full-export.pdf';

// FLAGS
const SKIP_SOURCES = true;   // Czy pomijać bibliografię/źródła (redukcja stron)
const COMPRESS_PDF = true;   // Czy odpalić Ghostscript na końcu?

// Utils
const normalizePath = (path) => (path.length > 1 && path.endsWith('/')) ? path.slice(0, -1) : path;
const isTaxonomy = (path) => path.includes('/tag/') || path.includes('/category/') || (path.includes('/series/') && path.includes('/blog/'));
const isListPage = (path) => path === '/blog' || path.includes('/blog/page/');
const isSourcePage = (path) => path.includes('/sources');

// --- ACTIONS ---

async function autoScroll(page) {
    await page.evaluate(async () => {
        await new Promise((resolve) => {
            let totalHeight = 0;
            const distance = 100;
            const timer = setInterval(() => {
                const scrollHeight = document.body.scrollHeight;
                window.scrollBy(0, distance);
                totalHeight += distance;
                if(totalHeight >= scrollHeight - window.innerHeight){
                    clearInterval(timer);
                    resolve();
                }
            }, 50);
        });
    });
}

async function expandAllContent(page) {
    const clicked = await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        const expandBtn = buttons.find(b => {
            const text = b.innerText.toLowerCase();
            return text.includes('expand all') || text.includes('rozwiń');
        });
        if (expandBtn) {
            expandBtn.click();
            return true;
        }
        return false;
    });
    if (clicked) await new Promise(r => setTimeout(r, 1000));
}

// --- CORE ---

async function crawlSite(browser) {
    console.log(`🕷️  Phase 1: Discovery Crawl (Skip Sources: ${SKIP_SOURCES})...`);
    const page = await browser.newPage();
    const queue = ['/', '/404-test'];
    const visited = new Set();
    const discoveredPages = [];

    while (queue.length > 0) {
        const currentPath = normalizePath(queue.shift());
        if (visited.has(currentPath)) continue;
        visited.add(currentPath);

        // FILTRY
        if (isTaxonomy(currentPath)) continue;
        if (SKIP_SOURCES && isSourcePage(currentPath)) {
            // process.stdout.write(`\r⏩ Skipping source: ${currentPath}`); // Opcjonalne logowanie
            continue;
        }

        try {
            await page.goto(`${BASE_URL}${currentPath}`, { waitUntil: 'networkidle0' });

            const newLinks = await page.evaluate((baseUrl) => {
                return Array.from(document.querySelectorAll('a'))
                    .map(a => a.href)
                    .filter(href => href.startsWith(baseUrl) && !href.includes('#') && !href.match(/\.(png|jpg|pdf|xml|json|zip)$/i))
                    .map(href => new URL(href).pathname);
            }, BASE_URL);

            for (const link of newLinks) {
                const norm = normalizePath(link);
                // Dodajemy do kolejki tylko jeśli nie jest źródłem (gdy flaga aktywna)
                const shouldSkipSource = SKIP_SOURCES && isSourcePage(norm);
                
                if (!visited.has(norm) && !queue.includes(norm) && !isTaxonomy(norm) && !shouldSkipSource) {
                    queue.push(link);
                }
            }

            if (!isListPage(currentPath)) {
                const dateStr = await page.evaluate(() => {
                    const time = document.querySelector('time');
                    if (time) return time.getAttribute('datetime');
                    const meta = document.querySelector('meta[property="article:published_time"]');
                    return meta ? meta.content : null;
                });

                let type = 'misc';
                if (currentPath.startsWith('/books/')) type = 'book';
                else if (currentPath.startsWith('/blog/')) type = 'blog';
                else if (currentPath === '/' || currentPath.startsWith('/about') || currentPath.startsWith('/contact')) type = 'core';

                discoveredPages.push({ path: currentPath, type, date: dateStr ? new Date(dateStr) : null });
                process.stdout.write(`\r🔎 Found: ${discoveredPages.length} pages...`);
            }
        } catch (e) { /* ignore */ }
    }
    console.log(`\n✅ Found ${discoveredPages.length} pages.`);
    return discoveredPages;
}

function sortPages(pages) {
    console.log('🗂️  Phase 2: Sorting...');
    const core = pages.filter(p => p.type === 'core').sort((a, b) => a.path.localeCompare(b.path));
    const books = pages.filter(p => p.type === 'book').sort((a, b) => a.path.localeCompare(b.path));
    const blog = pages.filter(p => p.type === 'blog').sort((a, b) => {
        if (a.date && b.date) return b.date - a.date; 
        return a.path.localeCompare(b.path);
    });
    const misc = pages.filter(p => !['core', 'book', 'blog'].includes(p.type)).sort((a, b) => a.path.localeCompare(b.path));

    const home = core.find(p => p.path === '/');
    return [...(home ? [home] : []), ...core.filter(p => p.path !== '/'), ...books, ...blog, ...misc];
}

async function printPages(browser, sortedPages) {
    console.log('🖨️  Phase 3: Printing...');
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 1600 });
    const buffers = [];

    for (let i = 0; i < sortedPages.length; i++) {
        const item = sortedPages[i];
        process.stdout.write(`\n📸 [${i + 1}/${sortedPages.length}] ${item.path}`);

        try {
            await page.goto(`${BASE_URL}${item.path}`, { waitUntil: 'networkidle0' });
            await expandAllContent(page);
            process.stdout.write(' [Scroll]');
            await autoScroll(page);
            await new Promise(r => setTimeout(r, 1000));

            await page.evaluate((slug) => {
                const old = document.getElementById('print-slug-header');
                if (old) old.remove();
                const h = document.createElement('div');
                h.id = 'print-slug-header';
                h.innerHTML = `<div style="font-family: monospace; font-size: 12px; font-weight: bold; color: #000; border-bottom: 2px solid #000; padding: 5px 0; margin-bottom: 20px;">SLUG: ${slug} | ADAM KORGA (BACKUP)</div>`;
                document.body.prepend(h);
            }, item.path);

            const buffer = await page.pdf({
                format: 'A4',
                printBackground: true, 
                margin: { top: '20mm', bottom: '20mm', left: '15mm', right: '15mm' }
            });
            buffers.push(buffer);
        } catch (e) {
            console.error(` ❌ Error: ${e.message}`);
        }
    }
    return buffers;
}

(async () => {
  const browser = await puppeteer.launch({ headless: "new" });
  const rawPages = await crawlSite(browser);
  const sortedPages = sortPages(rawPages);
  const pdfBuffers = await printPages(browser, sortedPages);
  await browser.close();

  if (pdfBuffers.length > 0) {
      console.log(`\n🔗 Phase 4: Merging...`);
      const mergedPdf = await PDFDocument.create();
      for (const b of pdfBuffers) {
        const pdf = await PDFDocument.load(b);
        (await mergedPdf.copyPages(pdf, pdf.getPageIndices())).forEach(p => mergedPdf.addPage(p));
      }
      
      // Zapisz wersję RAW
      const rawOutput = COMPRESS_PDF ? 'temp_raw.pdf' : OUTPUT_FILE;
      await fs.writeFile(rawOutput, await mergedPdf.save());
      
      if (COMPRESS_PDF) {
          console.log(`\n📦 Phase 5: Compression (Ghostscript)...`);
          try {
              // Używamy dokładnie Twoich flag: /ebook = ~150dpi images
              const cmd = `gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook -dNOPAUSE -dQUIET -dBATCH -sOutputFile="${OUTPUT_FILE}" "${rawOutput}"`;
              
              execSync(cmd, { stdio: 'inherit' });
              
              // Sprzątanie
              await fs.unlink(rawOutput);
              console.log(`✅ Success! Compressed file saved: ./${OUTPUT_FILE}`);
          } catch (e) {
              console.error('❌ Compression failed. Is Ghostscript installed?');
              console.error(e.message);
              // Fallback: zmieniamy nazwę temp na output
              await fs.rename(rawOutput, OUTPUT_FILE);
              console.log('⚠️  Saved uncompressed version instead.');
          }
      } else {
          console.log(`✅ Success! File saved: ./${OUTPUT_FILE}`);
      }
  }
})();