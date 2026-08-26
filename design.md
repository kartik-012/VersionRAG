# design.md
### VersionRAG — Production UI/UX Design Specification

---

# 1. Design Philosophy

VersionRAG's interface exists to answer one question, always, without ambiguity: **"Which version is this, and where did it come from?"** Every other design decision is subordinate to that.

**Priorities, in order:**
1. Clarity — the user should never have to guess what they're looking at
2. Trust — every AI answer must be visibly grounded in evidence
3. Evidence-first — sources are never optional or hidden
4. Version awareness — active version context is always visible
5. Simplicity — no decoration without function
6. Accessibility — usable by keyboard, screen reader, and reduced-motion users
7. Consistency — the same component behaves the same way everywhere
8. Speed — perceived performance matters as much as real performance
9. Professional product quality — this should feel like an internal tool a serious engineering org actually depends on

**The UI should feel:** modern, intelligent, calm, technical, trustworthy, premium, production-ready.

**The UI must avoid:** excessive gradients, unnecessary glassmorphism, excessive animation, giant marketing sections, decorative UI with no function, fake AI effects (typing shimmer for its own sake, fake "thinking" animations with no real status behind them), portfolio-style presentation.

---

# 2. Design System

## Colors

| Token | Purpose |
|---|---|
| `primary` | Main brand/action color — used for primary buttons, active nav item, links |
| `secondary` | Supporting actions, secondary buttons |
| `accent` | Sparingly used highlight — e.g., "new" badges |
| `background` | App-wide base background |
| `surface` | Card/panel background, one step lighter/darker than background |
| `border` | All dividers, card outlines, input borders |
| `text` | Primary text color |
| `muted-text` | Secondary/metadata text (timestamps, labels) |
| `success` | Completed states, positive confirmations |
| `warning` | Degraded states, low-but-not-zero confidence |
| `error` | Failures, destructive actions |
| `info` | Neutral informational callouts |

**Version colors:** each version gets a deterministically-assigned color from a fixed palette (not random per render), reused identically across the version selector, version badges, comparison view, citations, timelines, and charts. This consistency is non-negotiable — a version's color must mean the same thing everywhere on screen at all times.

**Change colors:**
- `change-added` — distinct from success (added ≠ good, just added)
- `change-removed` — distinct from error (removed ≠ failure, just removed)
- `change-modified` — a third distinct hue, not a blend of added/removed

**Rule:** color is never the only signal. Every colored state (added/removed/modified, confidence levels, processing status) also has an icon and/or text label, for colorblind users and for scanning speed.

## 3. Typography

| Level | Use |
|---|---|
| H1 | Page titles only (one per page) |
| H2 | Major section headers |
| H3 | Card/panel titles |
| H4 | Sub-section labels |
| Body | Default reading text |
| Small | Metadata, timestamps, helper text |
| Caption | Micro-labels under icons, table footnotes |
| Code | Monospace, used for version identifiers, API paths, code snippets — never use body font for a version string like `v15.14.0` |
| Data/Numbers | Tabular figures (monospace numerals) so numbers in tables and comparisons align vertically |

**Font family:** one sans-serif for UI text (system font stack or a single licensed sans like Inter), one monospace for code/version identifiers/citations. Do not mix additional decorative fonts.

**Priority:** long technical documents must remain readable at length — body text line-height and measure (line length) are tuned for reading, not just for compact screens.

---

# 4. Spacing & Layout

- **Spacing scale:** a single 4px-based scale (4, 8, 12, 16, 24, 32, 48, 64) used everywhere — no arbitrary one-off pixel values.
- **Border radius:** one small radius for inputs/buttons, one slightly larger radius for cards/modals. Do not mix more than two radius values across the app.
- **Container widths:** a max content width for reading-focused screens (document reader, answer view) so text doesn't stretch edge-to-edge on wide monitors; full-width for data-dense screens (comparison tables, change explorer).
- **Sidebar width:** fixed width on desktop, collapses to icon-only or hidden on smaller viewports.
- **Header height:** fixed and consistent across every screen.
- **Modal sizing:** small (confirmations), medium (forms), large (evidence/document preview) — three sizes only.
- **Grid:** a consistent column grid underlies all layouts, so cards, tables, and panels align predictably across screens.

**Device priority:** desktop is the primary experience (documents and comparisons need horizontal space), but tablet and mobile must remain fully usable, not just "not broken."

---

# 5. UI Component System

Each component below must define: purpose, states, interaction, accessibility requirements, loading state, and error state where applicable.

| Component | Key states beyond default |
|---|---|
| Button | default / hover / active / disabled / loading (spinner replaces label, width doesn't jump) |
| Input | default / focus / error / disabled / with helper text |
| Textarea | same as Input + auto-resize behavior defined |
| Select / Dropdown | default / open / disabled / with search (for long lists like version selection) |
| Tabs | active / inactive / disabled; keyboard arrow-navigable |
| Modal | entry/exit transition defined; focus is trapped inside while open; Esc closes |
| Drawer | used for mobile sidebar and evidence panel; slides from edge |
| Tooltip | hover + keyboard-focus triggered, not click-only |
| Toast | success / error / info variants; auto-dismiss with pause-on-hover |
| Badge | used for version tags, change-type tags, status tags — fixed small set of variants |
| Avatar | user initials fallback when no image |
| Card | default / hover (only where the card is clickable) / selected |
| Table | sortable columns, sticky header on scroll, row hover state |
| Pagination | current page always visible, disabled state for boundary pages |
| Breadcrumb | truncates gracefully on narrow screens |
| Command Menu | keyboard-first (Cmd/Ctrl+K), for jumping between documents/versions/projects |
| Search Bar | debounced input, clear button, loading indicator while searching |
| Version Selector | shows current version prominently, dropdown lists all versions in order with dates |
| Version Badge | color-coded per version, always paired with the version text label |
| Document Card | shows name, type, version count, latest version, last updated, processing status |
| Document Tree | expandable hierarchy: Family → Document → Versions |
| Citation | inline, clickable, visually distinct from body text (underline + icon, not just color) |
| Evidence Card | expandable, shows source text + document + version + section |
| Change Card | shows change type (with icon), old vs new, severity, confidence |
| Timeline | horizontal version sequence with change-count markers between versions |
| Progress Indicator | stage-based (not fake percentage) — shows named stage, not a spinner alone |
| Skeleton | matches the shape of the content it's replacing, never a generic gray box unrelated to layout |
| Empty State | icon + one-sentence explanation + one clear action |
| Error State | icon + what happened + why (if known) + what to do next |
| Confirmation Dialog | used for all destructive actions; requires explicit confirm, not a single accidental click |

---

# 6. Application Shell

```
┌─────────────────────────────────────────────────────────┐
│ Top Bar: Breadcrumbs | Search | Context Indicator | 🔔 | 👤│
├───────────┬───────────────────────────────┬─────────────┤
│           │                               │             │
│  Sidebar  │        Main Content           │  Evidence   │
│           │                               │  Panel      │
│ Workspace │                               │ (optional,  │
│ Projects  │                               │  collapsible)│
│ Documents │                               │             │
│ Versions  │                               │             │
│ Changes   │                               │             │
│ Queries   │                               │             │
│ Evaluations│                              │             │
│ Settings  │                               │             │
└───────────┴───────────────────────────────┴─────────────┘
```

- **Sidebar:** Workspace switcher at top, then Projects → Documents → Versions → Changes → Queries → Evaluations → Settings. Never more than one level of nesting visible at once — deeper items expand inline.
- **Top bar:** breadcrumbs (always shows full path: Workspace / Project / Document / Version), global search, a version/context indicator shown only on screens where a version is "active," notifications, user menu.
- **Right evidence panel:** appears only on the AI Query and Document Reader screens; collapsible so it doesn't crowd users who don't need it right now.

**Rule:** the navigation must never grow past these seven top-level items without a deliberate redesign — resist adding more just because a feature needs a home.

---

# 7. Dashboard

Shows, each linking directly to the relevant screen:
- Recent projects (with quick-open)
- Recent documents (with processing status inline)
- Processing status summary (X processing, Y failed, Z ready)
- Version activity (recently added versions)
- Recent queries (so users can revisit an earlier question)
- Detected changes (most recent, with severity)
- Evaluation status (last benchmark run date + headline number, if one exists)

**Rule:** no vanity metrics. A number on the dashboard must lead somewhere useful when clicked — "12 documents" links to the document list, not nowhere.

---

# 8. Workspace & Projects

- **Workspace creation:** single-step form (name only required at minimum).
- **Workspace switcher:** dropdown from the top-left, shows all workspaces the user belongs to, clearly separated from "Create new workspace."
- **Project creation:** name + optional description, scoped to the active workspace.
- **Project overview:** summary cards (documents, versions, changes, recent queries) plus a document list.
- **Project settings:** rename, delete (with confirmation), default query settings.
- **Members:** list with role badges (Owner/Admin/Member/Viewer), invite by email, role change dropdown per member.
- **Permissions:** a simple table showing what each role can do — visible to admins, not hidden logic.

**Rule:** the active workspace and project must always be visible in the breadcrumb — a user should never be uncertain which tenant's data they're viewing.

---

# 9. Document Management

Users can: upload, drag/drop, view, rename, delete, inspect metadata, see processing state, see version history, open a document.

**Document Card shows:**
```
[icon]  Node.js Assert Documentation
        Type: Technical Documentation
        Versions: 4  (latest: v17)
        Last updated: 2 days ago
        Status: ● Ready
```

Processing status uses a colored dot + text label (never color alone): Ready (success), Processing (info, animated subtly), Failed (error), Needs Review (warning — e.g., version detection had low confidence).

---

# 10. Version Management

This is the most important UI area in the product — get this right above everything else.

**Version Selector:** always shows the currently active version as a labeled, colored badge — never just a bare dropdown with no current-state indicator.

**Version Timeline (compact, used in document detail):**
```
v14 ──── v15 ──── v16 ──── v17 (current)
```
Each node is clickable, shows release date on hover, and the active/selected version is visually distinct (larger, filled, or outlined differently — not color alone).

**Version detail panel shows:** version identifier, release date, previous/next version links, processing status, source document, document family, change summary count (added/removed/modified since previous version).

**Hard rule:** versions of the same document must NEVER visually resemble separate, unrelated documents. They always appear nested under their parent document (Document Tree, breadcrumb, document detail page) — never as flat, disconnected cards in a generic document list.

---

# 11. Version Comparison

```
┌─────────────────┐         ┌─────────────────┐
│   v14.21.3       │   VS    │   v15.14.0       │
└─────────────────┘         └─────────────────┘

Added (12)   Removed (3)   Modified (8)   Unchanged
```

- **Side-by-side mode:** two panes, synchronized scroll, changed sections highlighted in both.
- **Unified diff mode:** single column, inline +/- markers (styled like a code diff, using change-added/change-removed colors plus +/- symbols — never color alone).
- **Controls:** filter by change type, search within changes, jump-to-section navigation, "inspect evidence" opens the Evidence Card inline, "open original source" opens the Document Reader at that exact location.

---

# 12. Change Timeline

```
v14
 │
 ├─ [Modified] assert.deepEqual() behavior changed
 ├─ [Deprecated] assert.CallTracker
 │
v15
 │
 ├─ [Added] assert.partialDeepStrictEqual()
 ├─ [Removed] legacy error format  ⚠ silent change
 │
v16
```

Each change entry shows: change type (icon + label), one-line description, old version → new version, an "evidence" link, and source location.

**Explicit vs. implicit/silent changes must be visually distinguished** — a silent (undocumented) change gets a distinct icon and a short explanatory label ("detected automatically — not in changelog"), never presented identically to a documented change.

---

# 13. AI Query Interface

This is the primary product experience — a serious workspace, not a generic chat bubble UI.

```
┌───────────────────────────────────────────────────┐
│ Version: [v15.14.0 ▾]   Scope: [Current Version ▾] │
├───────────────────────────────────────────────────┤
│ Was function X stable in v15?                [Ask] │
└───────────────────────────────────────────────────┘

ANSWER
Function X was marked as a Release Candidate in
v15.14.0, not fully stable.

SOURCE VERSION: v15.14.0
CONFIDENCE: High

EVIDENCE
 └─ Node.js Assert Docs — v15.14.0 — Section "Stability"
    "assert.partialDeepStrictEqual is 1_2 - Release candidate"
    [View in document]

RELATED VERSIONS: v14 (Experimental) · v16 (Stable)
CHANGE REFERENCES: 1 related change between v14 → v15
```

Every answer carries: the answer text, the source version used, evidence (expandable), citations (clickable), a confidence state, related versions, and any relevant change references.

---

# 14. Version-Aware Query Controls

```
Version: [v15.14.0 ▾]
Scope:   [Current Version ▾]
```

**Scope options:** Current version / Specific version / Compare versions / All versions / Date range.

The selected scope is always shown directly above the question input, in a fixed, high-visibility position — never buried in a settings menu. If scope is "All versions" and the answer draws from multiple versions, the answer view must show which version each piece of evidence came from.

---

# 15. Answer + Evidence UI

An AI answer is never presented as an unsupported paragraph. Fixed structure:

```
ANSWER
[Generated answer text]

SOURCE VERSION
v15.14.0

CONFIDENCE
[High / Moderate / Low / Insufficient evidence]

EVIDENCE
[Expandable evidence snippet(s)]
[Citation(s)]
```

The evidence panel expands inline (not a separate page navigation) so the user never loses their place. Users can inspect the exact source chunk that produced the answer.

---

# 16. Citation Experience

Citations are interactive, not plain text. Clicking one opens a panel showing: document, version, section, page/location, source, and the relevant excerpt highlighted.

**Hard rule:** the UI must make it visually impossible to confuse "AI-generated statement" with "source evidence" — different background treatment, a distinct label ("Source" vs "Answer"), and citations are always rendered in the monospace/code-adjacent style reserved for sourced material.

---

# 17. Confidence UI

No raw, misleading percentages presented alone. Use meaningful states:

- **High confidence** — strong, consistent evidence
- **Moderate confidence** — evidence found, some ambiguity
- **Low confidence** — thin or indirect evidence
- **Insufficient evidence** — the system explicitly declines to guess

Each state can carry a short explanation when useful:
> "Moderate confidence — evidence was found in the requested version, but the source contains conflicting information."

A numeric score may exist underneath for internal/debug purposes, but the primary UI surface is always the named state plus explanation, never a bare "87%" with no context.

---

# 18. Document Reader

Includes: document title, active version (always visible), table of contents, sections, page navigation, in-document search, highlighted evidence (when arrived at via a citation), and citation anchors (stable links to a specific section/version).

**Key interaction:** clicking a citation anywhere in the app jumps directly into the Document Reader at that exact source location, with the relevant text highlighted.

---

# 19. Processing Experience

Named stages, shown in order, current stage highlighted:

```
Uploading → Validating → Parsing → Extracting metadata →
Detecting version → Creating chunks → Generating embeddings →
Detecting changes → Indexing → Ready
```

Failed state shows which stage failed and offers a retry action.

**Hard rule:** never show a fake numeric progress percentage when real progress isn't measurable — show the named current stage instead. A fabricated "73%" that doesn't correspond to anything real erodes trust the moment a user notices it stalling.

---

# 20. Empty / Loading / Error States

Every one of the following gets a dedicated, designed state (icon + message + action), never a blank screen or a raw error dump:

No documents · No versions · No changes · No search results · Processing · Failed processing · No evidence · Insufficient evidence · Unauthorized · Network failure · AI provider failure.

**Every error message states:** what happened, why (if known), and what the user can do next (retry, contact support, go back).

---

# 21. Accessibility

- Full keyboard navigation for every interactive element (tab order follows visual order)
- Visible focus states on all focusable elements (never `outline: none` without a replacement)
- Semantic HTML (`<nav>`, `<main>`, `<button>`, proper heading hierarchy) — not `<div>` soup with click handlers
- Screen-reader labels for icon-only buttons and status indicators
- Sufficient color contrast (WCAG AA minimum) across all text/background pairs, including badges
- `prefers-reduced-motion` respected — animations degrade to instant state changes
- Non-color indicators paired with every color-coded state, as established in Section 2
- Accessible forms (labeled inputs, associated error messages, not placeholder-only labels)
- Accessible tables (proper `<th>` scope, sortable-column state announced)

---

# 22. Responsive Design

| Breakpoint | Behavior |
|---|---|
| Desktop | Full shell: sidebar + main + evidence panel all visible |
| Tablet | Sidebar collapses to icon rail or drawer; evidence panel becomes an overlay |
| Mobile | Sidebar becomes a navigation drawer (hidden by default); evidence becomes an expandable bottom sheet; comparison view stacks vertically or becomes horizontally scrollable; tables remain scrollable within their container, never break layout; the active version indicator remains visible in the top bar at all times, on every breakpoint |

---

# 23. Motion

**Use subtle, functional animation only:** panel open/close transitions, loading-state transitions, state changes (e.g., a card transitioning from "Processing" to "Ready"), navigation transitions between related screens.

**Avoid:** parallax, decorative animated backgrounds, "AI thinking" animations that don't correspond to real work happening, animation for its own sake.

All motion respects `prefers-reduced-motion: reduce` by falling back to instant state changes.

---

# 24. UX Rules (Non-Negotiable)

1. Always show active version context.
2. Never hide evidence behind unnecessary interactions.
3. Never make the user guess processing status.
4. Never represent unsupported AI claims as facts.
5. Never rely only on color to communicate meaning.
6. Preserve user context when navigating (don't reset filters/scroll/selected version on back-navigation).
7. Keep destructive actions explicit (confirmation required, clearly labeled).
8. Make errors recoverable (retry paths, not dead ends).
9. Keep technical information scannable (tables and structured layouts over dense paragraphs).
10. Prefer progressive disclosure over clutter (advanced options collapsed by default, available on demand).

---

# 25. Screen Inventory

For each screen: Purpose, Primary user, Primary action, Secondary actions, Important information, Empty state, Loading state, Error state.

| Screen | Purpose | Primary Action |
|---|---|---|
| Authentication | Sign up / log in / reset password | Submit credentials |
| Dashboard | Orient the user, surface what needs attention | Navigate to a project/document |
| Workspace | Manage org-level settings and members | Switch or configure workspace |
| Project | Overview of one project's documents/activity | Open a document or ask a question |
| Documents | Browse/manage all documents in a project | Upload a new document |
| Document Detail | See one document's versions and history | Open a version or upload new version |
| Version Detail | Inspect one specific version | View content or compare |
| Version Comparison | Compare two versions directly | Review changes, inspect evidence |
| Change Timeline | See all changes across a document's lifetime | Filter/search changes |
| AI Query | Ask a question, get a version-grounded answer | Submit a question |
| Search Results | Find documents/versions/changes globally | Open a result |
| Document Reader | Read full document content in context | Read, search within document |
| Evidence Detail | Inspect the exact source behind an answer | Verify/trust the answer |
| Evaluations | View benchmark/accuracy results | Review a benchmark run |
| Settings | Configure account/project preferences | Update settings |
| Members | Manage who has access | Invite/remove/change role |
| Processing Details | Debug a stuck or failed ingestion job | Retry or investigate |

*(Empty/loading/error states for each screen follow the patterns defined in Sections 19–20 — not repeated per-screen here to avoid duplication; each screen's specific empty-state copy should be written during implementation, not invented here.)*

---

# 26. Design Implementation Rules

- Must translate cleanly into: Next.js, React, TypeScript, Tailwind CSS, and shadcn/ui (or an equivalent accessible component primitive library) — chosen specifically because these primitives already handle keyboard/focus/ARIA correctly, reducing the chance of accessibility regressions.
- Build reusable components (Section 5) — no page duplicates its own one-off button or card styling.
- No hard-coded visual values (colors, spacing, radius) scattered through component code — everything routes through design tokens (Section 2–4) defined once, referenced everywhere.
- Design tokens should be implemented as a single source of truth (e.g., a Tailwind config extension or a CSS variables file) so a future rebrand or dark-mode pass touches one place, not hundreds of components.
