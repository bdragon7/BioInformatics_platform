# Bioinformatics Studio UI/UX + Data Interaction Implementation Plan

## 1. Scope delivered in this iteration

Implemented foundation slices:
- Portable launchers (`main.py`, `.sh`, `.bat`, `.cmd`) with CLI args (`--project`, `--data`, `--workflow`, `--debug`)
- Modernized PySide6 shell with top bar, side nav, right info panel, and docked plugin manager
- Spreadsheet-style CSV data viewer widget with:
  - sorting
  - filtering/search
  - in-place editing
  - undo/redo edit history
  - row multi-selection summary
  - column statistics preview
  - export visible/filtered rows
- Theme system with light/dark/high-contrast modes
- Color management foundation:
  - scientific palettes registry
  - color picker dialog with alpha
  - recent/favorites palette storage

## 2. Widget design blueprint (next build targets)

## 2.1 ModernDataTable
- Base: `QTableView` + `QAbstractTableModel` + `QSortFilterProxyModel`
- Must-have:
  - multi-sheet tab container
  - virtual row provider for 10^6+ rows
  - freeze panes + pinned columns
  - header dropdown filters
  - per-column type enforcement + validation errors
  - regex find/replace + fill-down
  - include/exclude checkbox column
  - change tracking layer with modified-cell highlighting

## 2.2 SelectionLinkController
- Bi-directional syncing table <-> plots
- Selection sets (named snapshots)
- Criteria builder for row inclusion/exclusion

## 2.3 ColorPickerWidget (advanced)
- HSV wheel + saturation/value square
- RGB/HSL/HEX + opacity sliders
- harmony generator (complementary/analogous/triadic)
- color blindness simulator + contrast checker
- palette import/export (ASE/GPL/hex list)

## 2.4 Premium shell widgets
- CommandPalette overlay (`Ctrl+K`)
- NotificationToast queue
- ProgressWidget with cancellation
- PropertyPanel for contextual editing

## 3. Color palette specification

## 3.1 UI semantic tokens
- Primary: `#2563EB` (light), `#0EA5E9` (dark)
- Success: `#16A34A`
- Warning: `#F59E0B`
- Error: `#DC2626`
- Neutral text: `#1F2937` / `#E5E7EB`

## 3.2 Data viz defaults
- Categorical (color-blind safe): `#0072B2 #E69F00 #009E73 #D55E00 #CC79A7 #56B4E9`
- Continuous (viridis-like): `#440154 #414487 #2A788E #22A884 #7AD151 #FDE725`
- Diverging: `#2166AC #67A9CF #D1E5F0 #FDDBC7 #EF8A62 #B2182B`

## 4. Icon requirements

- Master source: SVG, artboard 1024x1024
- Exports:
  - `icon.ico` (16/24/32/48/64/128/256)
  - `icon.icns`
  - `icon.png` variants (16..512)
- Visual concept: DNA helix + node graph motif
- Stroke: 1.75px equivalent at 24px
- States:
  - idle
  - processing badge
  - error badge
  - update badge

## 5. UX quality bars

- command feedback < 100ms
- long operations show progress + cancel
- theme switch < 500ms
- startup target < 5s with cached config
- no UI thread blocking operations

## 6. UI/UX testing strategy

1. Visual regression screenshots across themes and 3 breakpoints (1024, 1366, 1920)
2. Interaction tests:
   - edit cell, undo/redo, export visible rows
   - filter + sort + multi-select workflows
3. Accessibility tests:
   - keyboard navigation
   - high-contrast mode
   - focus indicators
4. Performance tests:
   - 100k row load with virtual scrolling
   - stable interaction latency under filtering/sorting
5. Usability tests:
   - 5–10 researchers, task completion and SUS score

## 7. Incremental roadmap for these enhancements

- Sprint A: Multi-sheet + validation + exclusion column
- Sprint B: bidirectional selection linking with plots
- Sprint C: advanced color widget + palette IO + accessibility tools
- Sprint D: command palette, notifications, animations, saved layouts
- Sprint E: pivot/correlation/profile panels + formula engine
