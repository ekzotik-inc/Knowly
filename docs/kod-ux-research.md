# kod.ru UX research

Исследование начато 26 августа 2026 года по публичной главной странице kod.ru: https://kod.ru/.

На первом экране kod.ru использует чёткую editorial-иерархию: компактная строка последних публикаций, центральный логотип, горизонтальная тематическая навигация, затем крупный featured article с фотографией, заголовком поверх изображения, кратким описанием и автором. Рядом расположена плотная колонка свежих новостей с миниатюрами и временем публикации, а также отдельная колонка статей. Сайт поддерживает поиск через отдельный control и повторяет важные материалы в разных лентных блоках.

Для Knowly релевантны не цвета и не чужие изображения, а паттерны: hero card с крупным визуалом и overlay title, плотные карточки с thumbnail + metadata, тематические tabs, отдельная activity/news rail, ясные timestamp/status labels, persistent bottom assistant surface и responsive multi-column-to-single-column layout. Не переносить брендинг, тексты или изображения kod.ru.

## Article page findings

Открыта featured article `https://kod.ru/luchshie-igrovye-noutbuki-do-120k`. Страница строится вокруг editorial reading flow: breadcrumbs, category label, крупный title, author/avatar, view count, publication time, reading time, затем hero image. После hero есть блок «Содержание», CTA «Читайте в Telegram», lead paragraphs, blockquote/highlight and sequential sections.

Images are displayed as large high-quality content media with `object-fit`-style responsive sizing, descriptive alt text and explicit photo credits/captions such as `// Фото: MSI`. Images are embedded between text sections rather than confined only to card thumbnails. The article also exposes copy-link, discussion/share surfaces and a persistent bottom assistant/chat widget.

For Knowly this suggests a quiz/publication detail view with: creator avatar/character + title + compact metadata; large optional cover/photo with rounded pink-violet frame; a readable intro; question sections as interactive content blocks; sticky share action; and small creator/assistant surface. Do not reuse kod.ru assets, copy, or proprietary implementation.

## Knowly implementation review

The Knowly home screen now includes a `ТВОЯ ЛЕНТА` section with `Все игры` / `Мои` tabs, a new publication-feed structure, a featured first card, and an empty-publication state for users without tests. Each publication card has a branded cover treatment with the user's personal character, overlay title, category label, metadata, share action, and copy-link action. The implementation uses only Knowly-owned SVG character rendering and pink/magenta/violet gradients; no kod.ru images or gray palette was imported.

Local DOM verification confirmed the new feed tab controls and empty-publication CTA are present in the web app build. The first visual snapshot upload failed once and the browser later returned about:blank, so visual verification is supplemented by successful TypeScript/build checks and DOM text/control extraction.
