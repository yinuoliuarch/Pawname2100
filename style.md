# Interface and Visual Style

## Document role

This file is the source of truth for visual language, layout, interface hierarchy, responsive behavior, motion, and visitor-facing terminology. 

## 1. Design concept

The page is a playful **dog-name time machine** made from many rounded bubble-like panels. The names—not generic cartoon dogs—are the primary characters.

The interface should balance two voices:

- expressive, speculative, and playful for titles and names;
- precise and quiet for evidence, controls, counts, and limitations.

Do not make the experience fun merely by adding more colors. Fun should come from anticipation, responsive movement, transformation, and the personality of names.

## 2. Working title

The existing title **How to Name Your Dog in 100 Years** is temporary. Alternatives were discussed but none has been confirmed. Do not change the title until the user approves one.

Leading candidates include:

- **A Dog Named Tomorrow**
- **What New York Calls Its Dogs**
- **Copy, Invent, Repeat**
- **Names Yet to Be Called**
- **Calling the Future**

## 3. Typography

Use the embedded OFL-licensed [Modak](https://github.com/google/fonts/tree/main/ofl/modak) display typeface for:

- the main title;
- major result titles;
- the selected name in the history view.

The bubble treatment uses:

- dark fill;
- thin cream outline;
- dark offset depth;
- restrained soft shadow.

The title is a single uninterrupted line. Use responsive sizing to keep it inside the page without horizontal overflow, including on a phone. It is substantially smaller than the first bubble-font version and must not dominate the interactive project.

Use the monospaced interface typeface for:

- controls;
- body copy;
- numbers;
- map labels;
- chart labels;
- evidence and limitations.

Do not use the bubble face for long text or small controls.

## 4. Bubble panels and translucent material

The page should read as a field of separate rounded panels rather than one heavy dashboard box.

The material system is informed by [Apple's Materials guidance](https://developer.apple.com/design/human-interface-guidelines/materials), but it is a web interpretation rather than a native or exact Apple implementation.

Panel characteristics:

- translucent light surfaces;
- softly blurred color from the page background;
- internal white highlights;
- low-contrast gray or white contour lines;
- diffused shadows;
- rounded corners around 24–34 pixels;
- subtle saturation rather than opaque white.

Do not use heavy black outlines around primary panels. Dark contours remain acceptable for selected map areas, text, and high-priority buttons where contrast communicates interaction.

Apply the strongest glass treatment to functional layers:

- the centered control deck;
- map-and-results workspace;
- ranking rows and distribution summaries;
- technical settings;
- temporary progress status.

Use quieter translucent surfaces for content layers. Too many equally reflective panels would flatten the hierarchy.

## 5. Background

Use a warm, softly colored background that can be seen through the panels:

- warm cream as the base;
- yellow near the time controls;
- mint around spatial/data areas;
- restrained purple and blue ambient fields;
- a small amount of coral for warmth and intervention.

Ambient forms should be large, blurred, and non-semantic. They create depth but must not look like data marks.

## 6. Desktop composition

Center the primary interface at approximately 1240 pixels maximum width.

The introduction is compact enough that the simulation begins near the first viewport.

Desktop structure:

```text
Bubble title                         Project description
                                     Twin / Model / Simulation labels

NYC map with a thin floating control dock at its lower edge:
timeline above NYC area | exact-name search

NYC map, approximately 2/3 | Ranking/results, approximately 1/3

Collapsed technical settings

Quiet evidence and limitation cards
```

The timeline, area field, and exact-name search form a thin translucent dock spanning the map from left edge to right edge. It is spatially part of the map workspace rather than a separate page-wide section. Its lighter shadow, smaller radius, and tighter padding keep it elegant and secondary to the map. The map drawing reserves space above the dock so geography is not hidden behind it.

## 7. Primary controls

Use one aligned control deck for:

- **Choose a time**
- **NYC area**
- **Search a name across NYC**

Inputs and buttons have consistent heights. Use an eight-pixel spacing rhythm.

The timeline remains the primary manual interaction inside the dock. Give its scrubber the longest horizontal span, but keep the year compact. Play/pause is secondary to direct scrubbing. On narrow screens, place the dock in normal flow beneath the map so controls do not cover the geography.

Keep each search group linear on desktop: small label, compact field, compact button. Do not display a persistent success sentence beneath the area or name field; use hover titles, selected outlines, and result changes as feedback. Validation errors may still appear when needed.

Do not present the controls as a mandatory `1–2–3–4` sequence. Searching and ranking are alternative exploration paths.

Keep the Popular/Distinctive switch inside the ranking panel because it modifies those results.

Add a second segmented control near it:

```text
All | Boy | Girl | Shared
```

The visitor-facing labels Boy and Girl map to recorded `M/F`. Explain this in the supporting information below the workspace and in accessible descriptions, not as persistent prose beside the control. Shared is a derived usage category, not a third recorded gender.

## 8. Map and results

The map and ranking panel form one continuous workspace.

On desktop, this workspace is a constant-height frame. Changing the ranking lens, recorded-gender view, exact-name result, or name-history view must not resize the frame or push the page vertically. Longer result and history content scrolls inside its own side or detail panel. Tablet and phone layouts may return to content-driven height when the columns stack.

Keep the primary workspace operational rather than explanatory. It may show current year, area, result labels, counts, percentages, legends, loading states, validation errors, and controls. Method notes and caveats belong in the quieter supporting cards below the simulation.

Before name selection:

- the map selects NYC areas and communicates data availability;
- pale official NTA boundaries, restrained borough labels, and selected official neighborhood labels provide familiar orientation;
- neighborhood context remains non-interactive and does not imply that NTA and ZIP/ZCTA boundaries are equivalent;
- the selected area has a strong but refined outline;
- the Top 5 appears beside it.

Map navigation uses wheel/trackpad zoom, click-drag panning, small plus/minus controls, and a reset-view button. These controls remain visually quieter than selection and name-distribution color.

After name selection:

- recolor every area by the selected name's share;
- display a real visual legend from 0% to 5%+;
- show exact count and share in hover/focus text;
- keep the selected area identifiable.

Do not draw arrows that imply recorded movement or causal transmission.

Ranking hierarchy:

1. name;
2. count;
3. percentage;
4. origin color carried by the name card.

Do not show `H`, `M`, or `P` badges or a separate origin-icon legend in the primary workspace. Use the whole name card as the origin signal: yellow for historical records, mint for Markov invention, and purple for Cultural Pulse. Explain these colors once in the supporting information below the simulation, and retain origin wording in accessible labels and hover titles.

Align the two result selectors as compact, consistent rows. Each row uses the same label column and the same full-width segmented-control column:

```text
Ranking lens         Popular | Distinctive
Recorded-gender view All | Boy | Girl | Shared
```

Labels, button heights, padding, and control widths should line up. Do not place an explanatory paragraph between these selectors and the ranking.

## 9. Gender presentation

The gender view should feel like an analytical lens, not a demographic claim.

- **All:** complete annual group.
- **Boy:** recorded M group.
- **Girl:** recorded F group.
- **Shared:** names meeting the balance and evidence threshold.

Exact-name results should include a compact balance display:

```text
Recorded M count and percentage
Recorded F count and percentage
Shared / leans Boy / leans Girl / insufficient evidence
```

Avoid stereotypical pink/blue encoding. Use the existing palette with labels, line styles, or restrained variations that remain distinguishable without relying on gendered color conventions.

## 10. Motion and playfulness

Motion should explain state change rather than decorate everything.

Desired future motion:

- year readout gently stretches or wobbles while scrubbing;
- ranking bubbles move between positions rather than being replaced abruptly;
- a selected name expands from its ranking row into the distribution or history title;
- map areas brighten or softly rise when a name appears;
- Cultural Pulse produces a restrained purple ripple during active years;
- hover raises a ranking bubble slightly and previews its distribution.

Do not animate continuously. Respect `prefers-reduced-motion` and provide equivalent static feedback.

## 11. Loading and simulation feedback

Calculation time is part of the experience and must be visible.

- Preserve the last completed result while a new future calculates.
- Show progress in the primary workspace, not only in technical settings.
- Use language such as `Building one possible future · 68%`.
- Mark changed settings as needing a rerun.
- Confirm completion without implying prediction.

The expanded developer panel uses three balanced cards rather than four equal boxes:

1. **Naming mix** for local copying, citywide copying, and invention;
2. **Cultural Influence** for the seed, active period, and naming-group share;
3. **Run and model facts** for the random seed, selected-area targets, simulation period, five-year memory, Shared rule, and last completed run.

Keep percentages aligned with their labels and place each adjustable slider on a full row beneath its label. Let the panel height follow its content; do not preserve empty cards or artificial blank space merely to maintain a four-column grid.

## 12. Supporting information

The following cards sit visually in the background:

- **How it works**
- **Where numbers come from**
- **What it cannot see**

Use lighter gray typography, quieter translucent surfaces, and less shadow. They remain readable but must not compete with the simulation.

## 13. Color roles

- Yellow: time and simulation clock.
- Blue: selected state and quantitative map emphasis.
- Coral: intervention and primary action.
- Mint: invention.
- Purple: Cultural Pulse.
- Warm gray: neutral geography and contextual information.

Use color semantically and consistently. Do not assign pink and blue to gender.

## 14. Responsive behavior

### Desktop

- Keep map and ranking side by side.
- Keep the title and description in a compact two-column introduction.
- Center the control deck and workspace.

### Tablet

- Stack ranking below the map.
- Keep area and search inputs side by side where space permits.

### Phone

- Use one vertical column.
- Retain generous rounded panels and readable controls.
- Allow segmented controls to wrap or scroll without truncating labels.
- Keep the map large enough to select an area reliably.

## 15. Visitor language

Primary interface:

- **NYC area**, not ZIP or ZCTA;
- **annual naming group**, not cohort;
- **across NYC** or **NYC areas**, not citywide ZIP distribution;
- **Boy / Girl / Shared** with a clear method disclosure.

Technical settings and documentation retain ZIP, ZCTA, cohort, and recorded M/F where precision matters.

Possible playful phrases:

- `Choose a time`
- `Look inside an NYC area`
- `Find a name across NYC`
- `Meet the Top 5`
- `Building one possible future…`

Avoid overly cute microcopy that obscures evidence or model status.

## 16. Accessibility

- Maintain sufficient contrast on translucent panels.
- Do not communicate origin, gender view, or selection by color alone.
- Preserve keyboard access and visible focus states.
- Provide text equivalents for map values.
- Respect reduced-motion preferences.
- Ensure lighter supporting text remains comfortably readable.
- Keep the embedded font and all assets offline.
