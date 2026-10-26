# Source attribution and licensing scope

The root MIT license covers this project's original Python code, original analytical prose, and project documentation. It does not claim ownership of, or grant a new license over, third-party source records, geographic boundaries, factual reference aggregates, or optional dependencies. Retain source attribution and consult each provider's source terms when redistributing or adapting source data.

| Provider | Source | Identifier / URL |
| --- | --- | --- |
| City of Chicago | Building Permits | https://data.cityofchicago.org/Buildings/Building-Permits/ydr8-5enu |
| City of Chicago | Current ward boundaries, fixed to 2023 geography | https://data.cityofchicago.org/resource/p293-wvbd.json |
| Cook County Assessor | Single- and multi-family improvement characteristics | https://datacatalog.cookcountyil.gov/resource/x54s-btds.json |
| Cook County Assessor | Condominium unit characteristics | https://datacatalog.cookcountyil.gov/resource/3r7i-mrz4.json |
| Cook County Assessor | Commercial valuation | https://datacatalog.cookcountyil.gov/resource/csik-bsws.json |
| Cook County Assessor | Historical parcel universe | https://datacatalog.cookcountyil.gov/resource/nj4t-kc8j.json |
| Cook County Assessor | Parcel addresses | https://datacatalog.cookcountyil.gov/resource/3723-97qp.json |
| Cook County Assessor | Property class dictionary | https://raw.githubusercontent.com/ccao-data/data-architecture/master/dbt/seeds/ccao/ccao.class_dict.csv |
| A City That Works | Published dashboard aggregate benchmark | https://housing.acitythatworks.org/permitting |
| A City That Works | Original dashboard introduction | https://citythatworks.substack.com/p/introducing-our-housing-dashboard |

Exact requests, retrieval times, response digests, and selected-field definitions are in the frozen bundles and restored `data/raw/` directory. Acquisition code selects property attributes needed for the analysis; it does not request taxpayer or owner contact fields. Permit descriptions and property locations are public-source records and may still contain incidental source text. The archive contains data/metadata, not the publisher's executable app code.

The source snapshot was collected October 22, 2026. The report's cohort ends October 8, 2026. Annual assessor records are estimates and may lag physical change. Source terms are those of the original providers; no provider endorses these findings.

Optional notebook dependencies, matplotlib and numpy, are installed from their standard distributions and retain their own licenses. The original ChatGPT report app runtime and its vendored dependencies are not redistributed in this public repository.
