"""Prepare the observed records and map geometry for the dog-name sandbox.

Sources
-------
NYC Dog Licensing Dataset:
https://data.cityofnewyork.us/Health/NYC-Dog-Licensing-Dataset/nu7n-tubp

NYC ZIP Code Tabulation Areas:
https://data.cityofnewyork.us/City-Government/ZIP-Code-Tabulation-Areas/35j5-n34v

2020 Neighborhood Tabulation Areas:
https://data.cityofnewyork.us/City-Government/2020-Neighborhood-Tabulation-Areas-NTAs-Mapped/4hft-v355

Method references
-----------------
pandas duplicate handling:
https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.drop_duplicates.html

GeoPandas file input/output:
https://geopandas.org/en/stable/docs/user_guide/io.html

The script never modifies data/Original. It writes one compact JSON file and a
human-readable audit report to data/Processed.
"""

from __future__ import annotations

import html
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT / "data" / "Original"
PROCESSED = ROOT / "data" / "Processed"

DOG_CSV = ORIGINAL / "NYC_Dog_Licensing_Dataset_20260930.csv"
ZCTA_GEOJSON = ORIGINAL / "NYC_ZCTA_35j5-n34v.geojson"
NTA_GEOJSON = ORIGINAL / "NYC_2020_NTA_9nt8-h7nd.geojson"

OUTPUT_JSON = PROCESSED / "simulation_data.json"
OUTPUT_REPORT = PROCESSED / "preparation_report.json"

HISTORICAL_YEARS = list(range(2018, 2023))
VALID_BIRTH_YEAR_MIN = 1900
VALID_BIRTH_YEAR_MAX = 2026
INVENTED_NAME_MIN_LENGTH = 2
INVENTED_NAME_MAX_LENGTH = 12
SHARED_MINIMUM_CITY_COUNT = 20
SHARED_MINIMUM_M_SHARE = 0.35
SHARED_MAXIMUM_M_SHARE = 0.65
NTA_SIMPLIFY_TOLERANCE_DEGREES = 0.00035

PLACEHOLDER_NAMES = {
    "UNKNOWN",
    "NAME NOT PROVIDED",
    "NAME",
    "NAN",
    "NONE",
    "NONAME",
    "NO NAME",
    "NOT PROVIDED",
    "N/A",
    "NA",
}


def normalize_text(value: Any) -> str:
    """Normalize case and spacing while preserving Unicode and punctuation."""
    if pd.isna(value):
        return ""
    text = html.unescape(str(value))
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text.strip())
    return text.upper()


def normalize_zip(value: Any) -> str:
    """Return a five-digit ZIP string, or an empty string when unsupported."""
    if pd.isna(value):
        return ""
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return ""
    if not numeric.is_integer():
        return ""
    integer = int(numeric)
    if integer < 10000 or integer > 99999:
        return ""
    return f"{integer:05d}"


def markov_eligible(name: str) -> bool:
    """Apply the approved character and length rules for invention training."""
    if not INVENTED_NAME_MIN_LENGTH <= len(name) <= INVENTED_NAME_MAX_LENGTH:
        return False
    if " " in name or any(character.isdigit() for character in name):
        return False
    if not name[0].isalpha() or not name[-1].isalpha():
        return False
    allowed_punctuation = {"-", "'", "’"}
    return all(character.isalpha() or character in allowed_punctuation for character in name)


def is_placeholder_name(name: str) -> bool:
    """Match approved exact placeholders and malformed UNKNOWN variants."""
    return name in PLACEHOLDER_NAMES or name.startswith("UNKNOWN")


def repeated_units(name: str) -> list[tuple[int, str]]:
    """Detect adjacent repeated units of two or three Unicode letters."""
    letters = "".join(character for character in name if character.isalpha())
    found: set[tuple[int, str]] = set()
    for size in (2, 3):
        for index in range(len(letters) - 2 * size + 1):
            unit = letters[index : index + size]
            if letters[index + size : index + 2 * size] == unit:
                found.add((size, unit))
    return sorted(found)


def sample_records(frame: pd.DataFrame, columns: list[str], limit: int = 8) -> list[dict[str, Any]]:
    """Create JSON-safe sample records for the audit report."""
    if frame.empty:
        return []
    return json.loads(frame.loc[:, columns].head(limit).to_json(orient="records"))


def log_step(number: int, label: str, before: int, after: int) -> None:
    removed = before - after
    print(f"{number}. {label}: {before:,} -> {after:,} rows ({removed:,} removed)")


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    audit: dict[str, Any] = {
        "sources": {
            "dog_licenses": "https://data.cityofnewyork.us/Health/NYC-Dog-Licensing-Dataset/nu7n-tubp",
            "zcta_boundaries": "https://data.cityofnewyork.us/City-Government/ZIP-Code-Tabulation-Areas/35j5-n34v",
            "nta_boundaries": "https://data.cityofnewyork.us/City-Government/2020-Neighborhood-Tabulation-Areas-NTAs-Mapped/4hft-v355",
        },
        "steps": [],
        "excluded_examples": {},
    }

    # 1. Read the three original files without modifying them.
    dogs = pd.read_csv(DOG_CSV, low_memory=False)
    zctas = gpd.read_file(ZCTA_GEOJSON)
    ntas = gpd.read_file(NTA_GEOJSON)
    if zctas.crs is None:
        raise ValueError("The ZCTA boundary file has no coordinate reference system.")
    zctas = zctas.to_crs("EPSG:4326")
    if ntas.crs is None:
        raise ValueError("The NTA boundary file has no coordinate reference system.")
    ntas = ntas.to_crs("EPSG:4326")
    print(f"1. Read dog licenses: {len(dogs):,} rows, {len(dogs.columns)} columns")
    print(f"   Read ZCTA boundaries: {len(zctas):,} features, CRS {zctas.crs}")
    print(f"   Read NTA boundaries: {len(ntas):,} features, CRS {ntas.crs}")
    audit["input"] = {
        "dog_rows": int(len(dogs)),
        "dog_columns": list(dogs.columns),
        "zcta_features": int(len(zctas)),
        "zcta_crs": str(zctas.crs),
        "nta_features": int(len(ntas)),
        "nta_crs": str(ntas.crs),
        "dog_sample": sample_records(dogs, list(dogs.columns), 8),
    }

    # 2. Remove byte-for-byte duplicate rows.
    before = len(dogs)
    exact_duplicate_mask = dogs.duplicated(keep="first")
    audit["excluded_examples"]["exact_duplicates"] = sample_records(
        dogs.loc[exact_duplicate_mask], list(dogs.columns)
    )
    dogs = dogs.loc[~exact_duplicate_mask].copy()
    log_step(2, "Remove exact duplicate rows", before, len(dogs))
    audit["steps"].append({"step": 2, "label": "exact duplicates", "before": before, "after": len(dogs)})

    # 3. Remove repeated copies of the same license period across extract years.
    before = len(dogs)
    license_period_columns = [column for column in dogs.columns if column != "Extract Year"]
    repeated_period_mask = dogs.duplicated(subset=license_period_columns, keep="first")
    audit["excluded_examples"]["repeated_license_periods"] = sample_records(
        dogs.loc[repeated_period_mask], list(dogs.columns)
    )
    dogs = dogs.loc[~repeated_period_mask].copy()
    log_step(3, "Remove repeated license periods across extracts", before, len(dogs))
    audit["steps"].append({"step": 3, "label": "repeated license periods", "before": before, "after": len(dogs)})

    # 4. Normalize the fields used by the rule; preserve copied-name punctuation.
    dogs["_name"] = dogs["AnimalName"].map(normalize_text)
    dogs["_gender"] = dogs["AnimalGender"].map(normalize_text)
    dogs["_breed"] = dogs["BreedName"].map(normalize_text)
    dogs["_birth_year"] = pd.to_numeric(dogs["AnimalBirthYear"], errors="coerce")
    dogs["_zip"] = dogs["ZipCode"].map(normalize_zip)
    print(f"4. Normalize names, gender, breed, birth year, and ZIP: {len(dogs):,} rows retained")
    audit["steps"].append({"step": 4, "label": "normalize fields", "before": len(dogs), "after": len(dogs)})

    # 5. Remove missing and documented placeholder names.
    before = len(dogs)
    invalid_name_mask = dogs["_name"].eq("") | dogs["_name"].map(is_placeholder_name)
    audit["excluded_examples"]["missing_or_placeholder_names"] = sample_records(
        dogs.loc[invalid_name_mask], ["AnimalName", "AnimalBirthYear", "ZipCode"]
    )
    placeholder_counts = dogs.loc[invalid_name_mask, "_name"].value_counts(dropna=False).to_dict()
    dogs = dogs.loc[~invalid_name_mask].copy()
    log_step(5, "Remove missing and placeholder names", before, len(dogs))
    audit["placeholder_counts"] = {str(key or "<MISSING>"): int(value) for key, value in placeholder_counts.items()}
    audit["steps"].append({"step": 5, "label": "missing or placeholder names", "before": before, "after": len(dogs)})

    # 6. Remove invalid birth years, then retain the agreed 2018-2022 seed window.
    before = len(dogs)
    invalid_year_mask = dogs["_birth_year"].isna() | ~dogs["_birth_year"].between(
        VALID_BIRTH_YEAR_MIN, VALID_BIRTH_YEAR_MAX
    )
    audit["excluded_examples"]["invalid_birth_years"] = sample_records(
        dogs.loc[invalid_year_mask], ["AnimalName", "AnimalBirthYear", "ZipCode"]
    )
    dogs = dogs.loc[~invalid_year_mask].copy()
    dogs["_birth_year"] = dogs["_birth_year"].astype(int)
    log_step(6, "Remove invalid birth years", before, len(dogs))
    audit["steps"].append({"step": 6, "label": "invalid birth years", "before": before, "after": len(dogs)})

    before = len(dogs)
    outside_window_mask = ~dogs["_birth_year"].isin(HISTORICAL_YEARS)
    audit["excluded_examples"]["outside_seed_window"] = sample_records(
        dogs.loc[outside_window_mask], ["AnimalName", "AnimalBirthYear", "ZipCode"]
    )
    dogs = dogs.loc[~outside_window_mask].copy()
    log_step(7, "Retain AnimalBirthYear 2018-2022", before, len(dogs))
    audit["steps"].append({"step": 7, "label": "2018-2022 seed window", "before": before, "after": len(dogs)})

    # 8. Keep only five-digit ZIPs represented by the official boundary file.
    boundary_zips = set(zctas["zcta5"].astype(str).str.zfill(5))
    before = len(dogs)
    invalid_zip_mask = dogs["_zip"].eq("")
    audit["excluded_examples"]["invalid_zip_codes"] = sample_records(
        dogs.loc[invalid_zip_mask], ["AnimalName", "AnimalBirthYear", "ZipCode"]
    )
    dogs = dogs.loc[~invalid_zip_mask].copy()
    log_step(8, "Remove missing or non-five-digit ZIP values", before, len(dogs))
    audit["steps"].append({"step": 8, "label": "invalid ZIP values", "before": before, "after": len(dogs)})

    before = len(dogs)
    unmatched_zip_mask = ~dogs["_zip"].isin(boundary_zips)
    audit["unmatched_zip_counts"] = {
        str(key): int(value)
        for key, value in dogs.loc[unmatched_zip_mask, "_zip"].value_counts().sort_values(ascending=False).items()
    }
    audit["excluded_examples"]["zip_not_in_boundary_file"] = sample_records(
        dogs.loc[unmatched_zip_mask], ["AnimalName", "AnimalBirthYear", "ZipCode"]
    )
    dogs = dogs.loc[~unmatched_zip_mask].copy()
    log_step(9, "Match license ZIPs to official ZCTA boundaries", before, len(dogs))
    audit["steps"].append({"step": 9, "label": "ZIP boundary match", "before": before, "after": len(dogs)})

    # 9. Approximate unique dogs using the approved identity fields.
    identity_columns = ["_name", "_gender", "_birth_year", "_breed", "_zip"]
    identity_sizes = dogs.groupby(identity_columns, dropna=False).size().sort_values(ascending=False)
    repeated_identities = identity_sizes.loc[identity_sizes > 1]
    audit["approximate_identity"] = {
        "fields": identity_columns,
        "repeated_groups": int(len(repeated_identities)),
        "rows_in_repeated_groups": int(repeated_identities.sum()),
        "largest_groups": [
            {
                "name": index[0],
                "gender": index[1],
                "birth_year": int(index[2]),
                "breed": index[3],
                "zip": index[4],
                "license_period_rows": int(count),
            }
            for index, count in repeated_identities.head(20).items()
        ],
    }
    before = len(dogs)
    dogs = dogs.drop_duplicates(subset=identity_columns, keep="first").copy()
    log_step(10, "Collapse approved approximate dog identities", before, len(dogs))
    audit["steps"].append({"step": 10, "label": "approximate dog identities", "before": before, "after": len(dogs)})

    # 10. Audit the recorded gender field and exclude unsupported values rather
    # than silently assigning them to M or F.
    unsupported_gender_mask = ~dogs["_gender"].isin(["M", "F"])
    unsupported_gender_counts = dogs.loc[unsupported_gender_mask, "_gender"].value_counts(dropna=False)
    audit["excluded_examples"]["missing_or_unsupported_gender"] = sample_records(
        dogs.loc[unsupported_gender_mask], ["AnimalName", "AnimalGender", "AnimalBirthYear", "ZipCode"]
    )
    audit["gender_exclusions"] = {
        "count": int(unsupported_gender_mask.sum()),
        "values": {str(key or "<MISSING>"): int(value) for key, value in unsupported_gender_counts.items()},
    }
    before = len(dogs)
    dogs = dogs.loc[~unsupported_gender_mask].copy()
    log_step(11, "Retain supported recorded gender values M/F", before, len(dogs))
    audit["steps"].append(
        {"step": 11, "label": "supported recorded gender values", "before": before, "after": len(dogs)}
    )

    # 11. Aggregate the twin as year + ZIP + recorded gender + normalized name.
    grouped_long = (
        dogs.groupby(["_birth_year", "_zip", "_gender", "_name"], as_index=False)
        .size()
        .rename(
            columns={
                "_birth_year": "year",
                "_zip": "zip",
                "_gender": "gender",
                "_name": "name",
                "size": "count",
            }
        )
    )
    grouped = (
        grouped_long.pivot_table(
            index=["year", "zip", "name"], columns="gender", values="count", aggfunc="sum", fill_value=0
        )
        .reset_index()
        .rename(columns={"M": "m_count", "F": "f_count"})
    )
    for column in ["m_count", "f_count"]:
        if column not in grouped:
            grouped[column] = 0
        grouped[column] = grouped[column].astype(int)
    grouped["count"] = grouped["m_count"] + grouped["f_count"]
    grouped = grouped.sort_values(["year", "zip", "count", "name"], ascending=[True, True, False, True])
    print(
        f"12. Aggregate historical twin: {len(dogs):,} approximate dogs -> "
        f"{len(grouped_long):,} gender-name rows -> {len(grouped):,} compact name rows"
    )
    audit["steps"].append(
        {
            "step": 12,
            "label": "year + ZIP + recorded gender + name aggregation",
            "before": len(dogs),
            "after": len(grouped_long),
            "compact_rows": len(grouped),
        }
    )

    # 12. Derive constant annual totals and fixed M/F targets for each ZIP.
    annual_zip_counts = (
        dogs.groupby(["_zip", "_birth_year"]).size().unstack(fill_value=0).reindex(columns=HISTORICAL_YEARS, fill_value=0)
    )
    cohort_sizes: dict[str, int] = {}
    gender_targets: dict[str, dict[str, int]] = {}
    zero_cohort_zips: list[str] = []
    for zip_code, row in annual_zip_counts.iterrows():
        rounded_size = int(math.floor(float(row.mean()) + 0.5))
        if rounded_size > 0:
            cohort_sizes[zip_code] = rounded_size
            zip_gender_counts = dogs.loc[dogs["_zip"].eq(zip_code), "_gender"].value_counts()
            zip_total = int(zip_gender_counts.sum())
            m_share = float(zip_gender_counts.get("M", 0) / zip_total) if zip_total else 0.5
            m_target = int(math.floor(rounded_size * m_share + 0.5))
            gender_targets[zip_code] = {"M": m_target, "F": rounded_size - m_target}
        else:
            zero_cohort_zips.append(zip_code)
    audit["cohort_sizes"] = {
        "method": "Rounded mean approximate dogs born annually from 2018 through 2022",
        "zip_count": len(cohort_sizes),
        "minimum": int(min(cohort_sizes.values())) if cohort_sizes else 0,
        "maximum": int(max(cohort_sizes.values())) if cohort_sizes else 0,
        "median": float(pd.Series(cohort_sizes.values()).median()) if cohort_sizes else 0,
        "total_annual_cohort": int(sum(cohort_sizes.values())),
        "excluded_zero_cohort_zips": zero_cohort_zips,
    }
    gender_counts = dogs["_gender"].value_counts()
    city_m = int(gender_counts.get("M", 0))
    city_f = int(gender_counts.get("F", 0))
    gender_by_zip: dict[str, dict[str, Any]] = {}
    for zip_code, subset in dogs.groupby("_zip", sort=True):
        counts = subset["_gender"].value_counts()
        total = int(counts.sum())
        m_count = int(counts.get("M", 0))
        f_count = int(counts.get("F", 0))
        gender_by_zip[str(zip_code)] = {
            "M": m_count,
            "F": f_count,
            "M_share": m_count / total if total else None,
            "F_share": f_count / total if total else None,
            "annual_targets": gender_targets.get(str(zip_code), {"M": 0, "F": 0}),
        }

    city_name_gender = dogs.groupby(["_name", "_gender"]).size().unstack(fill_value=0)
    if "M" not in city_name_gender:
        city_name_gender["M"] = 0
    if "F" not in city_name_gender:
        city_name_gender["F"] = 0
    city_name_gender["total"] = city_name_gender["M"] + city_name_gender["F"]
    city_name_gender["m_share"] = city_name_gender["M"] / city_name_gender["total"]
    shared_all_window = city_name_gender.loc[
        city_name_gender["total"].ge(SHARED_MINIMUM_CITY_COUNT)
        & city_name_gender["m_share"].between(SHARED_MINIMUM_M_SHARE, SHARED_MAXIMUM_M_SHARE, inclusive="both")
    ]
    shared_by_year: dict[str, int] = {}
    for year, subset in dogs.groupby("_birth_year"):
        table = subset.groupby(["_name", "_gender"]).size().unstack(fill_value=0)
        m = table["M"] if "M" in table else pd.Series(0, index=table.index)
        f = table["F"] if "F" in table else pd.Series(0, index=table.index)
        total = m + f
        share = m / total
        shared_by_year[str(int(year))] = int(
            (total.ge(SHARED_MINIMUM_CITY_COUNT) & share.between(SHARED_MINIMUM_M_SHARE, SHARED_MAXIMUM_M_SHARE)).sum()
        )
    audit["gender_audit"] = {
        "M": city_m,
        "F": city_f,
        "total": city_m + city_f,
        "M_share": city_m / (city_m + city_f),
        "F_share": city_f / (city_m + city_f),
        "names_used_by_both_recorded_groups": int(((city_name_gender["M"] > 0) & (city_name_gender["F"] > 0)).sum()),
        "shared_rule": {
            "minimum_citywide_count": SHARED_MINIMUM_CITY_COUNT,
            "minimum_M_share": SHARED_MINIMUM_M_SHARE,
            "maximum_M_share": SHARED_MAXIMUM_M_SHARE,
        },
        "shared_names_across_2018_2022_combined": int(len(shared_all_window)),
        "shared_names_by_birth_year": shared_by_year,
        "by_zip": gender_by_zip,
    }
    print(
        "13. Derive constant annual groups and M/F targets: "
        f"{len(cohort_sizes):,} ZIPs, {sum(cohort_sizes.values()):,} approximate dogs per simulated year"
    )

    # 13. Measure the approved two- and three-character repetition structures.
    distinct_names = sorted(set(grouped["name"]))
    eligible_names = [name for name in distinct_names if markov_eligible(name)]
    repeating_names: list[str] = []
    unit_counts: Counter[str] = Counter()
    for name in eligible_names:
        units = repeated_units(name)
        if units:
            repeating_names.append(name)
            unit_counts.update(f"{size}:{unit}" for size, unit in units)
    repetition_rate = len(repeating_names) / len(eligible_names) if eligible_names else 0.0
    audit["name_rules"] = {
        "distinct_names": len(distinct_names),
        "markov_eligible_distinct_names": len(eligible_names),
        "invented_name_min_length": INVENTED_NAME_MIN_LENGTH,
        "invented_name_max_length": INVENTED_NAME_MAX_LENGTH,
        "repeated_unit_sizes": [2, 3],
        "names_with_repeated_units": len(repeating_names),
        "observed_repetition_rate": repetition_rate,
        "top_repeated_units": unit_counts.most_common(30),
        "repeating_name_examples": repeating_names[:80],
    }
    print(
        "14. Measure repeated units: "
        f"{len(repeating_names):,} of {len(eligible_names):,} eligible distinct names ({repetition_rate:.2%})"
    )

    # 14. Convert the aggregation to compact [name, M count, F count] arrays.
    historical: dict[str, dict[str, list[list[Any]]]] = {}
    for (year, zip_code), subset in grouped.groupby(["year", "zip"], sort=True):
        historical.setdefault(str(int(year)), {})[str(zip_code)] = [
            [str(row.name), int(row.m_count), int(row.f_count)] for row in subset.itertuples(index=False)
        ]

    # 15. Keep only needed ZCTA geometry fields and attach annual-group metadata.
    zctas = zctas[["zcta5", "intptlon", "intptlat", "geometry"]].copy()
    zctas["zcta5"] = zctas["zcta5"].astype(str).str.zfill(5)
    zctas["cohort"] = zctas["zcta5"].map(cohort_sizes).fillna(0).astype(int)
    zctas["has_data"] = zctas["cohort"].gt(0)
    zcta_features = json.loads(zctas.to_json(drop_id=True))

    # 16. Derive a quiet offline neighborhood-reference layer. Representative
    # points keep labels inside multipart NTAs; simplified boundaries reduce the
    # embedded page size. This layer is orientation only, never a data join.
    ntas = ntas[["nta2020", "ntaname", "boroname", "geometry"]].copy()
    label_points = ntas.geometry.representative_point()
    ntas["label_lon"] = label_points.x
    ntas["label_lat"] = label_points.y
    ntas["geometry"] = ntas.geometry.simplify(NTA_SIMPLIFY_TOLERANCE_DEGREES, preserve_topology=True)
    nta_features = json.loads(ntas.to_json(drop_id=True))

    def nearby_nta_name(row: Any) -> str:
        try:
            lon = float(row.intptlon)
            lat = float(row.intptlat)
        except (TypeError, ValueError):
            return ""
        point = gpd.GeoSeries.from_xy([lon], [lat], crs="EPSG:4326").iloc[0]
        matches = ntas.loc[ntas.geometry.covers(point), "ntaname"]
        return str(matches.iloc[0]) if not matches.empty else ""

    zctas["nearby_nta"] = zctas.apply(nearby_nta_name, axis=1)
    zcta_features = json.loads(zctas.to_json(drop_id=True))
    audit["nta_reference_layer"] = {
        "role": "visual orientation only; no dog records were reassigned",
        "original_features": int(audit["input"]["nta_features"]),
        "retained_features": int(len(ntas)),
        "simplification_tolerance_degrees": NTA_SIMPLIFY_TOLERANCE_DEGREES,
        "labels": "official representative points generated inside each NTA geometry",
    }

    simulation_data = {
        "meta": {
            "title": "How to Name Your Dog in 100 Years",
            "observed_years": HISTORICAL_YEARS,
            "simulation_start": 2023,
            "simulation_end": 2126,
            "memory_years": 5,
            "default_seed": 2126,
            "default_local_copy_percent": 70,
            "default_citywide_copy_percent": 25,
            "default_invention_percent": 5,
            "default_pulse_duration_years": 5,
            "default_pulse_strength_percent": 5,
            "pulse_duration_range_years": [1, 20],
            "pulse_strength_range_percent": [0, 20],
            "distinctive_score": "local share minus citywide share",
            "distinctive_minimum_local_count": 2,
            "shared_minimum_city_count": SHARED_MINIMUM_CITY_COUNT,
            "shared_minimum_m_share": SHARED_MINIMUM_M_SHARE,
            "shared_maximum_m_share": SHARED_MAXIMUM_M_SHARE,
            "record_status": "Reconstructed approximate dogs from dog-license periods",
        },
        "cohort_sizes": cohort_sizes,
        "gender_targets": gender_targets,
        "historical": historical,
        "historical_names": distinct_names,
        "name_rules": audit["name_rules"],
        "zcta": zcta_features,
        "nta": nta_features,
    }

    # 17. Validate invariants, then write only derived files to data/Processed.
    if city_m + city_f != len(dogs):
        raise AssertionError("Gender counts do not equal the reconstructed dog total.")
    if int(grouped["count"].sum()) != len(dogs):
        raise AssertionError("Compact historical M/F counts do not reconstruct the dog total.")
    if any(target["M"] + target["F"] != cohort_sizes[zip_code] for zip_code, target in gender_targets.items()):
        raise AssertionError("At least one annual M/F target does not equal its fixed annual group.")
    with OUTPUT_JSON.open("w", encoding="utf-8") as stream:
        json.dump(simulation_data, stream, ensure_ascii=False, separators=(",", ":"))
    with OUTPUT_REPORT.open("w", encoding="utf-8") as stream:
        json.dump(audit, stream, ensure_ascii=False, indent=2)

    print(f"15. Preserve recorded gender: M {city_m:,} + F {city_f:,} = {city_m + city_f:,}")
    print(f"16. Prepare NTA context: {len(ntas):,} official neighborhood features")
    print(f"17. Write browser data: {OUTPUT_JSON} ({OUTPUT_JSON.stat().st_size / 1_000_000:.2f} MB)")
    print(f"18. Write audit report: {OUTPUT_REPORT} ({OUTPUT_REPORT.stat().st_size / 1_000:.1f} KB)")
    print("Preparation complete. Review the counts before building index.html.")


if __name__ == "__main__":
    main()
