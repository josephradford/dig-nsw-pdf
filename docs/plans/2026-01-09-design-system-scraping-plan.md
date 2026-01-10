# Design System Scraping Plan

## Problem Statement

The NSW Design System website (designsystem.nsw.gov.au) has a clear 9-section navigation structure visible in the left sidebar menu. The current scraping approach starts from the homepage with `base_path: "/"` and recursively follows all internal links, which produces a flat list of 99 pages in arbitrary order rather than preserving the hierarchical navigation structure.

**Expected PDF Structure:**
```
1. About
   - What is Design System
   - Supporting different roles
   - Our ecosystem
   - What's happening
2. Design
   - Getting Started
   - Figma UI Kit
   - Extending
   - Theming
   - Guides
3. Develop
   - Getting Started
   - Theming
4. Core styles
   - Logo
   - Colour
   - Typography
   - [etc.]
5. Components
   - Accordion
   - Back to top
   - [50+ components]
6. Utility Classes
   - Background
   - Borders
   - [etc.]
7. Methods
   - Search & Filters
   - Maps
   - [etc.]
8. Templates
   - Homepage
   - Content
   - [etc.]
9. Contribute
   - Contribution criteria
   - Propose a new component
   - Build a new component
```

## Current Behavior

**Config:**
```json
{
  "section_name": "NSW Design System",
  "base_url": "https://designsystem.nsw.gov.au",
  "base_path": "/",
  "pages": [{"url": "https://designsystem.nsw.gov.au", "order": 1}]
}
```

**Issues:**
1. Starting from homepage and following all links loses navigation structure
2. No concept of sections/subsections in the output
3. Pages appear in link-discovery order, not logical navigation order
4. PDF has flat structure instead of matching the website's hierarchy

## URL Structure Analysis

Each main section has its own URL path pattern:

| Section | Base Path | Example URL |
|---------|-----------|-------------|
| About | `/docs/content/about/` | `/docs/content/about/what-is-design-system.html` |
| Design | `/docs/content/design/` | `/docs/content/design/getting-started.html` |
| Develop | `/docs/content/develop/` | `/docs/content/develop/getting-started.html` |
| Core styles | `/core/` | `/core/logo/index.html` |
| Components | `/components/` | `/components/accordion/index.html` |
| Utility Classes | `/docs/content/utilities/` | `/docs/content/utilities/background.html` |
| Methods | `/docs/content/methods/` | `/docs/content/methods/search.html` |
| Templates | `/templates/` | `/templates/index.html` |
| Contribute | `/docs/content/contribute/` | `/docs/content/contribute/contribution-criteria.html` |

## Proposed Solution

### Option A: Multiple Sections in Config (RECOMMENDED)

Define each main navigation section as a separate section in `urls_config.json`. Each section will be scraped independently and compiled into a single PDF with proper hierarchy.

**Implementation:**
1. Create 9 separate section definitions in config
2. Each section has its own `base_path` to limit recursive scraping
3. Use `section_name` to create top-level headings in PDF
4. Modify PDF compiler to support nested sections within a single document

**Advantages:**
- Preserves exact navigation structure
- Each section is isolated and can be scraped in parallel
- Clear, explicit configuration
- Reuses existing scraping infrastructure

**Disadvantages:**
- Requires manual configuration of all sections
- More verbose config file
- Need to modify PDF compiler to handle multi-section documents

### Option B: Navigation Menu Extraction

Write custom code to extract the navigation menu structure from the Design System homepage, then use that to drive the scraping.

**Implementation:**
1. Fetch homepage
2. Parse left sidebar navigation menu (likely a `<nav>` element with specific structure)
3. Extract section names and URLs dynamically
4. Generate section configuration programmatically
5. Scrape each section

**Advantages:**
- Automatically adapts if navigation changes
- Less manual configuration
- Guaranteed to match website structure

**Disadvantages:**
- More complex implementation
- Fragile if website HTML structure changes
- Harder to debug and maintain

### Option C: Design System-Specific Scraper

Create a separate scraper class specifically for the Design System that understands its navigation patterns.

**Advantages:**
- Can handle Design System-specific quirks
- Clean separation of concerns

**Disadvantages:**
- Code duplication
- Maintenance burden of two scrapers
- Doesn't leverage existing infrastructure

## Recommended Approach: Option A

### Implementation Steps

1. **Update `urls_config.json`**
   - Create 9 separate section entries
   - Each with appropriate `base_path` and starting URL
   - Set `section_name` to match navigation menu

2. **Modify PDF Compiler**
   - Current: Each section in config → separate PDF
   - New: Support combining multiple sections into one PDF
   - Add optional `parent_document` field to group sections

3. **Test & Validate**
   - Verify page order matches navigation menu
   - Check PDF bookmark/TOC structure
   - Ensure no duplicate or missing pages

### Example Config Structure

```json
{
  "document_name": "NSW Design System",
  "output_filename": "nsw-design-system.pdf",
  "metadata": {
    "title": "NSW Design System",
    "author": "Compiled from NSW Design System",
    "subject": "NSW Government Design System Documentation"
  },
  "sections": [
    {
      "section_name": "About",
      "base_url": "https://designsystem.nsw.gov.au",
      "base_path": "/docs/content/about",
      "max_depth": 3,
      "pages": [{
        "title": "What is Design System",
        "url": "https://designsystem.nsw.gov.au/docs/content/about/what-is-design-system.html",
        "order": 1
      }]
    },
    {
      "section_name": "Design",
      "base_url": "https://designsystem.nsw.gov.au",
      "base_path": "/docs/content/design",
      "max_depth": 3,
      "pages": [{
        "title": "Getting Started",
        "url": "https://designsystem.nsw.gov.au/docs/content/design/getting-started.html",
        "order": 1
      }]
    },
    // ... 7 more sections
  ]
}
```

### Code Changes Required

**main.py:**
- Support grouping multiple sections into one PDF document
- Detect `document_name` field in config to enable multi-section mode

**pdf_compiler.py:**
- Accept multiple section_data objects
- Create hierarchical TOC with section-level headings
- Ensure proper page numbering across sections

**urls_config.json:**
- Add new structure for Design System with 9 sections

### Alternative: Simpler Multi-Start-Point Approach

If modifying the PDF compiler is too complex, we could:
1. Define the 9 sections as in Option A
2. Keep them as separate "sections" in the config
3. Run the scraper to collect all pages
4. Post-process: merge the 9 scraped sections before PDF compilation
5. This preserves section order but requires less code changes

## Success Criteria

1. ✓ PDF has 9 top-level sections matching website navigation
2. ✓ Each section contains correct sub-pages in correct order
3. ✓ PDF table of contents reflects navigation hierarchy
4. ✓ No duplicate pages
5. ✓ No missing pages (except known 404s)
6. ✓ Bookmarks/anchors preserve internal linking

## Open Questions

1. Should we scrape recursively within each section, or only grab pages listed in the navigation menu?
   - Recommendation: Only nav menu pages to avoid cluttering with dynamically linked content

2. How to handle cross-section links in the PDF?
   - Should work automatically if URL mapping is comprehensive

3. Should we create section divider pages in the PDF?
   - Nice-to-have but not essential for MVP
