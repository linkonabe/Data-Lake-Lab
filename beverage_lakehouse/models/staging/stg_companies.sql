-- models/staging/stg_companies.sql

select *
from read_csv_auto('s3://raw-data/companies_house/beverage_alcohol_companies.csv')
