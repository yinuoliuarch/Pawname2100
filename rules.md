# Simulation Rules

## Document role

This file is the source of truth for data preparation, model behavior, simulation rules.

## Current status

- Implemented: historical twin; constant annual groups; simultaneous five-year simulation; gender-aware historical aggregation, annual targets, copying, and invention pools; anchored Markov invention; repeated units; Cultural Pulse families; automatic random seeds; Popular/Distinctive and All/Boy/Girl/Shared results; contextual map distribution; ZIP or neighborhood search; exact-name gender balance; and gender-aware name history.
- The project title is still undecided. Do not replace the current title with one of the proposed alternatives until the user confirms it.

## 1. Evidence categories

Use these labels consistently:

- **Observed:** values in the original NYC Dog Licensing Dataset and official ZCTA and NTA geometry.
- **Reconstructed:** approximate dog identities created from repeated license records.
- **Derived:** grouped counts, annual group sizes, shares, spread, distinctiveness, recorded-gender proportions, and Shared-name classification.
- **Assumed:** five-year memory, route percentages, fixed future group sizes, and classification thresholds.
- **Simulated:** all names and counts from 2023–2126.
- **Speculative:** Cultural Pulse and its generated name-family influence.

The simulation tests the consequences of explicit rules. It is not a prediction and does not demonstrate real-world cultural causation.

## 2. Historical twin

Use the NYC Dog Licensing Dataset fields:

- `AnimalName`
- `AnimalGender`
- `AnimalBirthYear`
- `BreedName`
- `ZipCode`
- license-period fields needed for auditing duplicate records

Use `AnimalBirthYear` as the cohort year. The seed window is 2018–2022.

Reconstruct an approximate dog identity using normalized:

```text
name + recorded gender + birth year + breed + ZIP
```

This approximation can merge different dogs that share the same attributes. It must be labeled reconstructed rather than observed.

Sources:

- [NYC Dog Licensing Dataset](https://data.cityofnewyork.us/Health/NYC-Dog-Licensing-Dataset/nu7n-tubp)
- [NYC ZIP Code Tabulation Areas](https://data.cityofnewyork.us/City-Government/ZIP-Code-Tabulation-Areas/35j5-n34v)
- [2020 Neighborhood Tabulation Areas](https://data.cityofnewyork.us/City-Government/2020-Neighborhood-Tabulation-Areas-NTAs-Mapped/4hft-v355)

Current reconstructed 2018–2022 population:

```text
Recorded M:  61,055
Recorded F:  49,968
Total:      111,023
```

The source field is administratively named `AnimalGender` and contains `M` and `F`. Technical documentation must say **recorded M/F** or **recorded gender**. It must not imply that the dataset observes identity, owner intention, or a nonbinary category.

## 3. Prepared data structure

Preserve recorded gender in the processed historical twin. Aggregate as:

```text
year + ZIP + recorded gender + normalized name -> number of reconstructed dogs
```

Also derive for every supported ZIP:

- total constant annual group size;
- historical M share and F share across 2018–2022;
- integer annual M and F target counts whose sum exactly equals the total group;
- missing or unsupported gender counts, even when zero.

The original files remain unchanged in `data/Original`. Derived outputs belong in `data/Processed`.

The compact processed/browser structures are:

```text
historical[year][ZIP] = [name, M count, F count][]
run.years[year][ZIP] = [name ID, M count, F count][]
gender_targets[ZIP] = {M, F}
```

The global registry stores each exact name once with its origin and first appearance. The official NTA features are simplified and embedded only as an orientation layer; dog counts remain attached to ZCTA.

## 4. Constant annual group

Each ZIP receives a constant annual cohort equal to its rounded mean number of reconstructed dogs born annually from 2018–2022.

The cohort always remains 100%. Settings redistribute naming routes but never add or remove dogs.

For the gender-aware model:

```text
annual M count = rounded annual group × historical ZIP M share
annual F count = annual group − annual M count
```

Therefore, for every ZIP and year:

```text
M count + F count = annual group size
```

Visitor language calls this an **annual naming group**. Technical documentation may call it a cohort. It is not the number of all living dogs in the ZIP.

## 5. Simulation clock and simultaneous update

The simulation runs annually from 2023 through 2126.

For each year:

1. Freeze the complete preceding five-year state.
2. Calculate the new M and F groups for every supported ZIP from that frozen state.
3. Add every ZIP simultaneously.
4. Remove the oldest year and add the new year to the rolling window.

ZIP processing order must not influence results within a year.

The five-year window represents active cultural memory, not dog lifespan. A name leaves the copying pool after five years without a new adoption. It can later return through invention or Cultural Pulse.

## 6. Ordinary naming routes

Default route assumptions:

```text
Local copying:    70%
Citywide copying: 25%
Invention:         5%
Total:           100%
```

- **Local copying:** choose from the same ZIP, same recorded-gender group, and preceding five years, weighted by dog count.
- **Citywide copying:** choose from the same recorded-gender group outside the ZIP during the preceding five years, weighted by dog count.
- **Invention:** generate a dataset-shaped name using the recorded-gender-specific anchored Markov model.

Local copying is adjustable from 0–100%. Invention is adjustable from 0–25%. Citywide copying is the remainder.

If a small ZIP has no eligible local pool for one recorded-gender group, fall back to the same-gender citywide pool. If that pool is also empty, use the all-gender citywide pool and count the event as a documented fallback.

## 7. Gender-aware naming and Shared names

### Visitor views

Provide four views:

```text
All | Boy | Girl | Shared
```

- **Boy** displays dogs recorded as `M`.
- **Girl** displays dogs recorded as `F`.
- **Shared** is a derived name classification, not a third dog gender.

The method and limitations must disclose the mapping from visitor labels to the recorded binary field.

### Shared-name rule

Recalculate Shared status citywide for every year. A name is Shared when:

```text
citywide total for the name >= 20 dogs
and
recorded M share is between 35% and 65%, inclusive
```

The minimum count and balance range are assumptions. A rare name does not receive a Shared label merely because it occurs once in each group. Names below the threshold are **insufficient evidence**, not gender-neutral.

Shared rankings combine M and F counts. Their denominator remains the complete annual naming group so shares remain comparable with the All view.

### Gender-aware invention and Cultural Pulse

- Build historical and rolling Markov models separately for recorded M and F.
- Preserve the same meaningful-invention constraints for both groups.
- The Cultural Pulse creates one shared citywide family and allocates pulse names proportionally to the ZIP's M and F annual targets.
- A name may become Shared through observed cross-group use, continued copying in both groups, invention in both groups, or Cultural Pulse distribution.

The model does not infer that a name is inherently masculine, feminine, or neutral. It reports simulated usage patterns.

## 8. Meaningful Markov invention

Use a character-level Markov model only for invention. Build each recorded-gender-specific invention model from:

```text
Observed 2018–2022 patterns: 60%
Rolling preceding-five-year patterns: 40%
```

Weight transitions by dog count. Use strict two-character context:

```text
local two-character transition
→ same-gender citywide two-character transition
```

Do not use a one-character fallback.

An invented candidate must:

- contain 2–9 letters, with optional internal hyphens or apostrophes;
- contain approximately one to four syllables, estimated from vowel groups;
- contain at least one vowel;
- contain no more than two consecutive consonants;
- avoid any one-, two-, or three-character unit occurring more than twice;
- begin and end with two-character combinations found in the anchored model;
- be absent from the current citywide five-year population.

The syllable rule is a pronounceability proxy, not linguistic verification. An old invention can disappear and later return.

The approach adapts the character-transition principle demonstrated by Sam Twidale's [Procedural Name Generator](https://www.samcodes.co.uk/project/markov-namegen/) and [Markov Namegen library](https://github.com/Tw1ddle/markov-namegen-lib), without adding a network dependency.

## 9. Repeated-unit structure

Repeated units are adjacent letter patterns, not verified syllables.

- Detect two- and three-character repetitions in eligible training names.
- Weight their influence by dog count.
- Apply no more than one repeated-unit operation to a candidate.
- Reject triple accumulation such as `NYNYNY`.
- Repeated endings must be a two-character consonant–vowel or vowel–consonant unit.

## 10. Cultural Pulse

Cultural Pulse is a speculative test of temporary exposure to a famous name such as `LABUBU` or `ELVIS`.

Controls:

```text
On/off
User-entered seed name
Start year: 2023–2126
Duration: 1–20 years, default 5
Strength: 0–20% of the full annual group, default 5%
```

Pulse strength applies to all naming decisions, not only invention. Total annual group size stays constant. Allocate pulse decisions across M and F targets proportionally, then divide the ordinary remainder using the current local/citywide/invention proportions.

At pulse start:

1. Extract two-character transitions, vowel rhythm, and repeated-unit structure from the seed.
2. Blend these traits with the anchored historical and rolling model.
3. Generate one citywide family of 4–6 validated variants.
4. Require at least four letters and at least two distinct letters retained from the seed.
5. Reject any result identical to the seed.
6. Weight two or three family members more strongly so the intervention can become visible.

After the pulse ends, remove the external advantage immediately. Previously created variants remain in the five-year population and can persist only through ordinary copying and invention.

Do not run a parallel no-pulse baseline.

## 11. Possible futures and random seeds

Every **Run Simulation** action receives a new automatic random seed.

- The user cannot enter the seed.
- Report the assigned seed after completion.
- A run is one complete interconnected future for all ZIPs and years.
- One run is not a prediction.

## 12. Rankings

**Popular** ranks exact names by count and share in the selected area, year, and active gender view.

**Distinctive** uses:

```text
selected-area share − NYC share
```

For Boy and Girl, calculate both shares within that recorded-gender population. For All and Shared, use the full annual naming group. Shared first filters names by the citywide Shared rule.

The current Distinctive minimum is two local dogs. This is a low-evidence assumption and should be reviewed before submission.

An invented name is not automatically distinctive. Preserve origin metadata when names are later copied.

## 13. Map, search, and history

Without a selected name, the map is an area-selection and data-availability overview.

When a name is selected or searched:

- normalize capitalization; do not use fuzzy matching;
- report citywide total and share;
- report selected-area total and share;
- report the number of NYC areas in which it appears;
- report recorded M count, F count, their percentages, and Shared/leaning/insufficient-evidence status;
- update all values when year, area, or gender view changes;
- recolor areas by name share using a 5%+ cap;
- allow entry to name history and return to the Top 5.

Map denominators follow the active view: M group for Boy, F group for Girl, and full annual group for All or Shared.

Name history shows total, Boy, and Girl trajectories and geographic spread. Mark Cultural Pulse years when relevant.

Do not draw transmission arrows because the model does not record causal movement paths.

## 14. Limitations

The system cannot observe:

- why an owner selected a name;
- whether an owner considered a name masculine, feminine, neutral, or unrelated to gender;
- gender identity beyond the dataset's recorded M/F field;
- owner demographics, language, income, or social networks;
- unlicensed dogs, renaming, adoption, or movement;
- real media exposure unless entered as Cultural Pulse;
- verified pronunciation, meaning, harm, or cultural appropriateness;
- future population, licensing, geography, or data-collection changes.

The Shared label describes balance in recorded usage under an explicit threshold. It is not a universal cultural judgment about a name.
