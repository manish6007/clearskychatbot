# customers

Customer information table containing customer profiles and contact details.

## Table Details

- **Database**: athena_db
- **Catalog**: AwsDataCatalog
- **Location**: s3://athena-datasource-cg/customers1

## Columns

| Column | Type | Description |
|--------|------|-------------|
| customerid | string | Unique identifier for the customer (Primary Key) |
| firstname | string | Customer's first name |
| lastname | string | Customer's last name |
| email | string | Customer's email address |
| phonenumber | string | Customer's phone number |

## Common Queries

- Get customer by ID: `SELECT * FROM customers WHERE customerid = 'xxx'`
- Search by name: `SELECT * FROM customers WHERE firstname LIKE '%name%' OR lastname LIKE '%name%'`
- Get all customers: `SELECT * FROM customers`

## Relationships

- **orders**: customers.customerid → orders.customerid (One to Many)
- A customer can have multiple orders

## Business Context

The customers table stores all registered customer information. It is the primary reference for customer identity and is linked to orders through the customerid field.
