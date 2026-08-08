# Design Philosophy & Guidelines

## 1. Design Philosophy
AI Employee OS aims to provide an "enterprise software feels like consumer software" experience. The design must be clean, highly responsive, and data-dense without feeling cluttered. The presence of AI should feel native and conversational, not bolted-on as an afterthought.

## 2. UI Guidelines
- **Framework:** Tailwind CSS v4 paired with Radix UI primitives (e.g., shadcn/ui components).
- **Themes:** The application must fully support both Light and Dark modes.
- **Layouts:** Use a collapsible sidebar for global navigation and a top bar for contextual actions and user profile management.

## 3. Design Tokens

### Typography
- **Primary Font:** Inter (or similar clean sans-serif like Roboto/Outfit) for all UI elements.
- **Headings:** Bold, high-contrast, strictly hierarchical (H1 for page titles, H2 for section headers).
- **Readability:** Body text should maintain a minimum contrast ratio of 4.5:1.

### Colors
- **Primary:** A distinct, trustworthy blue or indigo (e.g., Tailwind's `indigo-600`).
- **Surface (Backgrounds):** `slate-50` for light mode, `slate-950` for dark mode.
- **Borders:** Subtle outlines to define cards and table rows without dominating the visual hierarchy (`slate-200` in light, `slate-800` in dark).
- **Accents:** Semantic colors for status (Green for success/paid, Yellow for warning/pending, Red for error/overdue).

### Spacing
- Rely heavily on a 4px grid system (Tailwind's standard spacing scale: `p-2`, `m-4`, `gap-6`).
- Maintain generous padding inside cards and forms to ensure a breathable interface.

## 4. Reusable Components
All standard UI elements (Buttons, Inputs, Dialogs, Selects, Tables) must be implemented as reusable React components within the `src/components/ui` directory. Direct use of raw HTML elements with extensive Tailwind utility classes in page layouts should be avoided in favor of these abstracted components.

## 5. Accessibility (a11y)
- All interactive elements must be keyboard navigable.
- Provide ARIA labels for icon-only buttons.
- Ensure proper focus states are visible (avoid `outline-none` without providing a custom focus ring).

## 6. Responsive Strategy
- **Mobile:** The sidebar collapses into a hamburger menu. Data tables become horizontally scrollable or transform into stacked card layouts.
- **Tablet/Desktop:** Expanded sidebar, multi-column grid layouts for dashboards.
- The AI Chat interface must be a persistent drawer or a dedicated full-page view on mobile, and a side-panel on desktop.
