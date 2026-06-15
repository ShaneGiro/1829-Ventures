"""Canonical Dealroom export column registry.

This module is the **single source of truth** for Dealroom export column names.
Dealroom is the only import source in v1, and exports arrive as CSV or Excel.

Why this exists
---------------
Future Dealroom pulls may omit columns, but the column *names* are stable. When
Dealroom renames, adds, or removes a column, edit it here only — the parser
references these constants instead of hard-coding string literals, so a header
change never means hunting through parsing logic.

What's here
-----------
- ``TEMPLATE_COLUMNS``: the full, ordered set of columns from the most recent
  export (the 6.10.26 template). Used to generate the downloadable import
  template so the team can see/share the exact expected column names.
- ``DealroomColumn``: named constants for the subset of columns the importer
  actually maps into CRM records. Update a value here if Dealroom renames it.
- ``HEADER_MARKERS``: columns that must all be present for a row to be treated as
  the header row (Dealroom prefixes exports with metadata rows).
- ``SUPPORTED_UPLOAD_EXTENSIONS``: accepted upload file types.

To add a newly mapped column: add the name to ``TEMPLATE_COLUMNS`` (if not
already present) and add a ``DealroomColumn`` constant, then reference it in the
parser. To drop one: remove the parser reference; the registry can keep the name
so older exports still round-trip.
"""

from __future__ import annotations

from typing import Final

# ─── Accepted upload formats ──────────────────────────────────────────────────
# Dealroom exports as CSV or modern Excel. Legacy .xls (BIFF) is intentionally
# unsupported to avoid an extra dependency; re-save as .xlsx if needed.
SUPPORTED_UPLOAD_EXTENSIONS: Final[tuple[str, ...]] = (".csv", ".xlsx", ".xlsm")

# ─── Header detection ─────────────────────────────────────────────────────────
# A row is the header row only if it contains all of these columns. This lets the
# parser skip the leading Dealroom metadata rows (export URL + filter summary).
HEADER_MARKERS: Final[tuple[str, ...]] = ("ID", "Name", "Dealroom URL")


class DealroomColumn:
    """Named Dealroom column headers used by the importer.

    Each attribute's value is the exact header string Dealroom emits. Change the
    value here if Dealroom renames a column; nothing else needs to change.
    """

    # Identity / profile
    ID: Final[str] = "ID"
    NAME: Final[str] = "Name"
    DEALROOM_URL: Final[str] = "Dealroom URL"
    WEBSITE: Final[str] = "Website"
    TAGLINE: Final[str] = "Tagline"
    LONG_DESCRIPTION: Final[str] = "Long description"

    # Location
    HQ_CITY: Final[str] = "HQ city"
    HQ_STATE: Final[str] = "HQ state"
    HQ_COUNTRY: Final[str] = "HQ country"
    LATITUDE: Final[str] = "Latitude"
    LONGITUDE: Final[str] = "Longitude"

    # Stage / classification
    GROWTH_STAGE: Final[str] = "Growth stage"
    LAST_ROUND: Final[str] = "Last round"
    INDUSTRIES: Final[str] = "Industries"
    SUB_INDUSTRIES: Final[str] = "Sub industries"
    TAGS: Final[str] = "Tags"
    ALL_TAGS: Final[str] = "All tags"

    # Founders (parallel semicolon arrays — index i is one founder)
    FOUNDERS: Final[str] = "Founders"
    FOUNDERS_STATUSES: Final[str] = "Founders statuses"
    FOUNDERS_GENDERS: Final[str] = "Founders genders"
    FOUNDERS_UNIVERSITIES: Final[str] = "Founders universities"
    FOUNDERS_LINKEDIN: Final[str] = "Founders linkedin"
    FOUNDERS_BACKGROUNDS: Final[str] = "Founders backgrounds"

    # Funding rounds (parallel semicolon arrays — index i is one round)
    EACH_ROUND_TYPE: Final[str] = "Each round type"
    EACH_ROUND_AMOUNT: Final[str] = "Each round amount"
    EACH_ROUND_CURRENCY: Final[str] = "Each round currency"
    EACH_ROUND_DATE: Final[str] = "Each round date"
    EACH_ROUND_INVESTORS: Final[str] = "Each round investors"


# ─── Full export template (most recent: 6.10.26) ─────────────────────────────
# The complete, ordered column set. Future exports may contain a subset of these;
# the parser keys off names, not position, so missing columns are tolerated.
# Keep this in export order so the downloadable template mirrors a real Dealroom
# file. Edit this list when Dealroom changes its export schema.
TEMPLATE_COLUMNS: Final[tuple[str, ...]] = (
    "ID",
    "Name",
    "Dealroom URL",
    "Website",
    "Tagline",
    "Long description",
    "Address",
    "Street",
    "Street number",
    "Street and street number",
    "Zipcode",
    "HQ region",
    "HQ country",
    "HQ state",
    "HQ city",
    "Latitude",
    "Longitude",
    "World locations",
    "Custom HQ regions",
    "Founding location",
    "Team (Dealroom)",
    "Team (Editorial)",
    "Investors names",
    "Each investor type",
    "Lead investors",
    "Total funding (USD M)",
    "Last round",
    "Last funding amount",
    "Last funding date",
    "First funding date",
    "Seed year",
    "Ownerships",
    "Tags",
    "Client focus",
    "Revenue model",
    "Launch year",
    "Launch month",
    "Launch date",
    "Closing year",
    "Closing month",
    "Closing date",
    "Industries",
    "Sub industries",
    "Growth stage",
    "Website traffic estimate yearly growth",
    "Employees Range",
    "Employees latest number",
    "Employees (2016,2017,2018,2019,2020,2021,2022,2023,2024,2025,2026)",
    "Employees in HQ country (2016,2017,2018,2019,2020,2021,2022,2023,2024,2025,2026)",
    "Employee growth % (last 3 months)",
    "Employee growth % (last 6 months)",
    "Employee growth % (last 12 months)",
    "Profit (USD) (2016,2017,2018,2019,2020,2021,2022,2023,2024,2025,2026,2027)",
    "Profit margin (2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025,2026,2027)",
    "EBITDA (USD) (2016,2017,2018,2019,2020,2021,2022,2023,2024,2025,2026,2027)",
    "EBITDA margin (2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025,2026,2027)",
    "Revenue (USD) (2016,2017,2018,2019,2020,2021,2022,2023,2024,2025,2026,2027)",
    "Revenue growth (2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025,2026,2027)",
    "R&D margin (2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025,2026,2027)",
    "KPI currency",
    "Valuation",
    "Valuation currency",
    "Valuation (USD)",
    "Valuation date",
    "Historical valuations - dates",
    "Historical valuations - values (USD M)",
    "Historical valuations - yearly since 2010 (USD M)",
    "EV/Revenue (2017,2018,2019,2020,2021,2022,2023,2024,2025,2026,2027)",
    "EV/EBITDA (2017,2018,2019,2020,2021,2022,2023,2024,2025,2026,2027)",
    "Website traffic estimate 6 months",
    "Employees dates",
    "Employees values",
    "Facebook",
    "Twitter",
    "LinkedIn",
    "Google Play link",
    "iTunes",
    "Each round type",
    "Each round amount",
    "Each round currency",
    "Each round date",
    "Total rounds number",
    "Each round investors",
    "Logo",
    "Founders",
    "Founders statuses",
    "Founders genders",
    "Is serial founder (yes/no)",
    "Founders backgrounds",
    "Founders universities",
    "Founders company experience",
    "Founders first degree",
    "Founders first degree year",
    "Founders linkedin",
    "Is top past founder (yes/no)",
    "Founder is from top university (yes/no)",
    "Founders founded companies total funding",
    "Founders years of education",
    "Is founders first company",
    "Founders strength",
    "Public lists",
    "Company status",
    "App downloads latest estimate (iOS)",
    "App downloads 6 months estimate (iOS)",
    "App downloads 12 months estimate (iOS)",
    "App downloads latest estimate (Android)",
    "App downloads 6 months estimate (Android)",
    "App downloads 12 months estimate (Android)",
    "All tags",
    "Website traffic rank 3/6/12 months",
    "Employee rank 3/6/12 months",
    "App rank 3/6/12 months",
    "Number of alumni founders that raised > 10M",
    "Technologies",
    "Income streams",
    "Tech stack data (by PredictLeads)",
    "Trade register number",
    "Trade register name",
    "Trade register URL",
    "SDGs",
    "SDG core or side value",
    "Year company became unicorn",
    "PIC number",
    "Dealroom Signal - Rating",
    "Dealroom Signal - Completeness",
    "Dealroom Signal - Team strength",
    "Dealroom Signal - Growth rate",
    "Dealroom Signal - Timing",
    "Innovation corporate rank",
    "Number of patents",
)
