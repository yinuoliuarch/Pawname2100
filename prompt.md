## Overview


I’m building a playful, self-contained browser simulation that explores how dog names might spread across New York City between 2023 and 2126. The simulation should grow from the NYC Dog Licensing Dataset for 2018–2023. This is an assignment and an experimental sandbox, not a consumer product, so the model should be understandable and the experience should reward deliberate exploration rather than prioritizing instant results.

Begin by reviewing `AGENTS.md`, then create `rules.md` to document the data and simulation logic and `style.md` to document the interface and visual language. Use this prompt as the initial project brief and keep those two documents synchronized with the implementation as it develops.

The primary material is the [NYC Dog Licensing Dataset](https://data.cityofnewyork.us/Health/NYC-Dog-Licensing-Dataset/nu7n-tubp). Use the [NYC ZIP Code Tabulation Areas](https://data.cityofnewyork.us/City-Government/ZIP-Code-Tabulation-Areas/35j5-n34v) and the [2020 Neighborhood Tabulation Areas from the NYC Department of City Planning](https://data.cityofnewyork.us/City-Government/2020-Neighborhood-Tabulation-Areas-NTAs-Mapped/4hft-v355) to construct the offline map. The name-generation method should draw on [Sam Twidale’s Procedural Name Generator](https://www.samcodes.co.uk/project/markov-namegen/) and the associated [Markov Namegen library](https://github.com/Tw1ddle/markov-namegen-lib). The visual references are [Modak from Google Fonts](https://github.com/google/fonts/tree/main/ofl/modak) and [Apple’s guidance on materials](https://developer.apple.com/design/human-interface-guidelines/materials). Store untouched source material in the project’s original-data folder.

## The experience

The public interface should offer only five meaningful choices: year, NYC area, gender view, ranking lens, and exact-name search. The year is controlled through an interactive timeline and should be the largest, most active, and most manual interaction on the page. Visitors should be able to select an NYC area from the map or find one through a plain-language search. The gender control should offer All, Boy, Girl, and Shared; the ranking lens should switch between Popular and Distinctive; and exact-name search should reveal a name’s citywide count, distribution, and history. Do not expose any additional model assumptions in the visitor interface. Visitors are exploring a completed simulation run, while the developer controls how that run is produced.

Keep the simulation controls in a visibly separate developer panel. This panel needs controls for local copying, citywide copying, and invention percentages, as well as Cultural Pulse settings for on/off state, seed name, strength, start year, and duration. Each run should receive an automatically assigned random seed, which must be shown when the run finishes. Include a Run Simulation button, honest progress feedback, the selected area’s annual total and M/F targets, and diagnostics covering the five-year memory rule, Shared threshold, and fallback counts from the most recent run. Moving a slider must not change the visible future; changes take effect only after the user presses Run Simulation.

Some local computation time is acceptable. Do not hide that delay behind a fake or precomputed default future. During a rerun, keep the previous completed run visible, show meaningful progress, yield often enough for the page to remain responsive, and report the seed when the new run is complete.

## Data preparation

Create `prepare.py` to clean and aggregate the historical data while preserving the dataset’s recorded M/F field. Group the historical records by year, ZIP, recorded M/F value, and name. A compact browser structure that stores a name once with separate M and F counts is acceptable as long as it loses no information.

Have the preparation script produce `preparation_report.json` with a gender audit. It should report the reconstructed totals for M and F dogs, the number and examples of missing or unsupported gender values, the number of distinct names used by both recorded groups, citywide and per-ZIP M/F proportions, the Shared-name threshold and the number of historical names that meet it, and all exclusions and fallbacks. Following the specified cleaning rules, the expected result is 61,055 M records and 49,968 F records, for a total of 111,023. Treat these figures as validation targets to investigate, not values to force. Never silently assign an unknown value to either M or F.

Use a fixed annual naming-group size for every supported ZIP, with its derivation from the prepared historical data stated explicitly in `rules.md`. Then derive integer annual M and F targets from the ZIP’s reconstructed 2018–2022 proportions. Calculate the M target by rounding the annual group size multiplied by the ZIP’s historical M share, then define the F target as the annual group size minus the M target. These values must always sum to that ZIP’s fixed annual group size.

The preparation method must include exact-row duplicate removal, repeated license-period removal, placeholder-name removal, birth-year filtering, official ZCTA matching, a clearly documented approximate identity rule, repetition analysis, and simplified geometry. Record the count and effect of every cleaning step so that the resulting exclusions and fallouts can be audited.

The map also needs a familiar reference layer based on the official 2020 NYC Neighborhood Tabulation Areas. Keep the downloaded GeoJSON untouched in `data/Original` and write only simplified NTA outlines and label points into the processed simulation data. Preserve the official neighborhood and borough names. In `preparation_report.json`, record the original and retained feature counts, the simplification rule, and the source URL. NTAs are visual context only: do not spatially reassign dog records from ZCTAs to NTAs, because ZCTA remains the selectable data geography.

Run `prepare.py` in the configured dependency environment and inspect the counts produced at every stage. Do not embed the data in `index.html` until the processed output passes validation.

## Simulation behavior

Design the browser state so that each ZIP and year stores name counts separately for recorded M and F values. Register each historical name once in a global name registry, retain its origin and first-year metadata, and store its counts by ZIP, year, and recorded gender.

For every simulated year, process each ZIP’s M and F targets separately. Begin by allocating Cultural Pulse decisions when the pulse is active. Divide the remaining target among invention, local copying, and citywide copying. Local copies must come from the same recorded-gender pool within the previous five years. Citywide copies must come from the same recorded-gender pool outside the current ZIP. Inventions must come from the corresponding gender-specific anchored model. Whenever a pool is empty, use and document the defined fallback. All ZIP and gender updates for a year must be calculated simultaneously rather than allowing earlier updates to influence later ones.

Build separate M and F historical anchors and rolling Markov models. Use a 60 percent observed and 40 percent rolling blend, frequency weighting, strict two-character transitions, a documented pronunciation proxy, a repeated-unit limit, a five-year uniqueness rule, an explicit attempt limit, and a documented copying fallback.

Each run should generate one shared citywide Cultural Pulse family. Allocate pulse decisions proportionally across each ZIP’s M and F targets, but do not insert the seed name itself and do not change the total annual group size.

Shared is a derived usage classification, not a third recorded gender. For each year, a name qualifies as Shared only when its citywide M and F counts sum to at least 20 and its M share is between 0.35 and 0.65, inclusive. Cache the yearly classifications if that improves performance.

## Interface and visual behavior

Establish the visual direction in `style.md` before implementing it. The page should use a restrained Modak bubble title, a centered 1240-pixel primary workspace, separate translucent rounded panels, soft white and gray contours instead of heavy black borders, and an ambient warm background visible through the panels. On desktop, split the workspace between the map and results; on smaller screens, stack them responsively. Use quiet evidence cards with lighter text and show simulation progress in the main workspace. Avoid stereotypical pink and blue gender encoding.

Make the timeline the primary interaction. It should sit at the top of a thin translucent control dock floating over the bottom of the map, extending from the map’s left edge to its right edge. Reserve enough drawing space above it so that it does not cover important geography. The current year should be the clearest changing value in the workspace, while the scrubber receives the longest uninterrupted horizontal span in the dock. Keep the year prominent without turning it into a large banner, and show only a few legible anchor years rather than labeling every year.

Place the area search and exact-name search in a restrained second row beneath the scrubber. Keep each label, field, and button on one line, and do not add persistent success messages below the fields. Use light padding, a modest radius, and a shallow shadow so the dock feels like a floating layer rather than a divider. Add a small play/pause control, but keep direct manual scrubbing as the primary behavior. On narrow screens, move the dock back into normal document flow beneath the map so that it cannot obscure the geography.

Changing the year must immediately update the map, rankings, exact-name results, and history using the current completed run. It must never rerun the simulation.

Keep both map selection and text search available for finding an area. The embedded SVG map must work without network tiles and support wheel or trackpad zoom, click-drag panning, visible zoom-in and zoom-out buttons, and a reset-view control. A drag gesture must not accidentally select a ZCTA. Draw official NTA boundaries as a quiet, noninteractive reference layer, with restrained borough labels and a curated, collision-aware set of official neighborhood labels. Place the selectable ZCTA shapes above that layer with lighter fills and clear hover and selected states. Hover and selection should show the ZIP or ZCTA together with nearby official NTA context when available.

In visitor-facing language, call the selected geography an “NYC area.” Reserve “ZCTA” for the method and developer panels. Make it clear in the supporting information that familiar neighborhood labels are orientation aids and do not correspond exactly to ZIP boundaries. Neighborhood lines and labels should remain visually subordinate to the color used for name distribution. The empty map state should still provide orientation through borough names, subtle neighborhood outlines, useful neighborhood labels, and hover labels for selectable areas. Avoid the appearance of a conventional gray GIS basemap; the reference layer should use thin translucent contours and soft text that fit the bubble and liquid-glass visual language.

Place the All, Boy, Girl, and Shared segmented control near the Popular and Distinctive control. Arrange them as two compact rows that share a label column and a full-width segmented-control column. Both controls need accessible button states and keyboard behavior, and neither should rely on color alone. Do not place persistent explanatory prose in the ranking panel, and do not add origin, invented/historical, or pulse-only filters to the public interface.

In the All view, rankings use combined M and F counts with the full-group denominator. Boy uses M counts with the M-group denominator, and Girl uses F counts with the F-group denominator. Shared includes only names that pass the citywide threshold and ranks them by combined local count with the full-group denominator. Popular and Distinctive must work in every view, with Distinctive always comparing equivalent local and citywide denominators.

Use the full surface of each ranking card to encode origin: yellow for historical names, mint for Markov inventions, and purple for Cultural Pulse names. Do not add abbreviated H, M, or P badges or an icon legend. Include the origin wording in each card’s accessible label and hover title, and explain the colors in the supporting information below the workspace.

Exact-name search should show recorded M and F counts and shares, along with a balance classification of Shared, leans Boy, leans Girl, or insufficient evidence. It should also show the active-view total and map distribution. Changing the year, area, or gender view must update these results without clearing the selected name.

The map’s denominator depends on the active view. Boy uses the area’s M target or count, Girl uses its F target or count, and All and Shared use the full annual group. Begin with a 5 percent visual cap, then inspect its effect on the smaller gender groups. If the cap is misleading, report the evidence and propose a more defensible rule before changing it.

Create a separate developer panel without crowding the visitor workspace. Organize it into three content-driven cards named Naming Mix, Cultural Influence, and Run and Model Facts. Show the selected area’s fixed annual naming-group total and M/F targets; the current local, citywide, and invention percentages and their 100 percent sum; Cultural Pulse settings and active interval; the five-year memory window; the Shared rule; and the latest run’s random seed, duration, and fallback counts. Align each percentage with its label, give each slider a full-width row of its own, and allow the panel height to follow its content. Technical language such as ZIP/ZCTA, cohort/target, and Markov model is appropriate here.

The name-history view should show total, recorded M, and recorded F trajectories; geographic spread; origin and first appearance; and the pulse interval when relevant. Never describe a name as inherently masculine, feminine, or neutral.

Place the following disclosure in the supporting information below the primary workspace rather than beside the gender control: “Boy and Girl correspond to the dataset’s recorded M/F field. Shared is derived from balanced citywide usage with at least 20 dogs; it is not a recorded identity or universal cultural judgment.”

On desktop, keep the map-and-results workspace at a constant height across ranking, filtering, search, and history states, with overflow contained within the results or detail panel. Once the columns stack on tablet or phone, the workspace can return to a content-driven height. Keep descriptive method prose outside the primary frame. Current state, data values, chart labels, legends, loading feedback, and validation errors belong inside because they directly support interaction; contextual explanation belongs in the quieter evidence cards below. On narrow screens, allow the controls to wrap cleanly.

## Technical limits, performance, and validation

Create `data/Original` for untouched source files and write all derived files to `data/Processed`. The final deliverable must be a single self-contained `index.html` under 50 MB, with its CSS, JavaScript, processed data, simplified geometry, and display font embedded. It must make no runtime network requests: do not use a CDN, `fetch`, an online font, or map tiles. The page must open directly from disk while Wi-Fi is off. Do not add a framework or build system, and do not use Git unless I explicitly ask you to.

Build the simulation efficiently from the beginning. Use aggregated counts rather than individual dog objects, and cache or reuse citywide totals, gender statistics, and identical Markov models whenever safe. Yield periodically so progress can render. Never rerun while sliders are moving, and keep the previous completed future visible during later runs. Optimize enough to keep the page responsive, but do not trade away transparency merely to eliminate all waiting. A visible, finite delay is acceptable for this assignment.

Validate both the data and the interaction carefully. The preparation process should produce 111,023 reconstructed records, with M plus F equal to that total. If it does not, investigate and document the discrepancy rather than forcing the expected number. Every historical name count must equal the sum of its M and F counts for the same name, ZIP, and year. In every simulated ZIP and year, the M and F targets must sum to the fixed annual group, and neither the settings nor Cultural Pulse may change that group’s size.

Test the Shared rule at its boundaries: fewer than 20 citywide dogs must not qualify; exactly 20 with an M share of exactly 35 or 65 percent must qualify; values outside the balance interval must not qualify; and a name’s status must be able to change from year to year.

Test all four gender views with both Popular and Distinctive rankings. Search for clearly Boy-leaning, Girl-leaning, and Shared names. While a name remains selected, change the area and year and confirm that its search result and history update correctly. Test Cultural Pulse both on and off, rerun progress and status, desktop and narrow layouts, keyboard focus and labels, manual timeline scrubbing, play/pause, map orientation through borough and neighborhood context, area selection through both the map and text search, and developer diagnostics before and after a run.

Finally, verify the standalone artifact itself: the embedded JSON must parse, the JavaScript must run without console errors, no external asset request or `fetch` may occur, no placeholder font marker may remain, the file must stay below 50 MB, and it must work locally with Wi-Fi disabled.

## Documentation and handoff

As the project is implemented, complete `rules.md` and `style.md` so that they describe the finished system accurately. Record the preparation counts and fallouts, document the internal browser data structure, explain each major code section, cite the method and design sources, and report the tests and known limitations. Keep visual rules in `style.md` rather than mixing them into the model documentation.

The final handoff should include `prepare.py`, the completed outputs in `data/Processed`, the standalone `index.html`, and synchronized versions of `rules.md`, `style.md`, and `prompt.md`.
