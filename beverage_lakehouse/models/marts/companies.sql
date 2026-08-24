-- models/marts/companies.sql

with source as (
    select * from {{ ref('stg_companies') }}
),

cleaned as (
    select
        "CompanyName"                           as company_name,
        "CompanyNumber"                         as company_number,
        "CompanyStatus"                         as company_status,
        "RegAddress.AddressLine1"               as address_line_1,
        "RegAddress.PostTown"                   as address_town,
        "RegAddress.PostCode"                   as postcode,
        "IncorporationDate"                     as incorporation_date,
        split_part("SICCode.SicText_1", ' ', 1) as sic_code_primary,
        "SICCode.SicText_1"                     as sic_description_primary
    from source
)

select *
from cleaned
where company_status = 'Active'
-- Deliberately excludes 'Active - Proposal to Strike off', 'Liquidation',
-- and 'In Administration' statuses — companies in insolvency or strike-off
-- proceedings are not stable/useful entities for business analysis in this
-- context. Documented judgment call, not an oversight — see docs/week2-log.md.
