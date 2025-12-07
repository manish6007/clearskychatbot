# orders

Order transactions table containing order records and their status.

## Table Details

- **Database**: athena_db
- **Catalog**: AwsDataCatalog
- **Location**: s3://athena-datasource-cg/orders

## Columns

| Column | Type | Description |
|--------|------|-------------|
| orderid | string | Unique identifier for the order (Primary Key) |
| customerid | string | Reference to the customer who placed the order (Foreign Key → customers.customerid) |
| orderdate | string | Date when the order was placed (format: YYYY-MM-DD) |
| orderamount | string | Total amount of the order in currency |
| orderstatus | string | Current status of the order (e.g., 'Pending', 'Shipped', 'Delivered', 'Cancelled') |

## Common Queries

- Get order by ID: `SELECT * FROM orders WHERE orderid = 'xxx'`
- Get orders by customer: `SELECT * FROM orders WHERE customerid = 'xxx'`
- Get orders by date range: `SELECT * FROM orders WHERE orderdate BETWEEN 'start' AND 'end'`
- Get orders by status: `SELECT * FROM orders WHERE orderstatus = 'Shipped'`
- Total orders per day: `SELECT orderdate, COUNT(*) as order_count, SUM(CAST(orderamount AS DOUBLE)) as total_amount FROM orders GROUP BY orderdate`

## Relationships

- **customers**: orders.customerid → customers.customerid (Many to One)
- **order_items**: orders.orderid → order_items.orderid (One to Many)
- Each order belongs to one customer and can contain multiple order items

## Business Context

The orders table is the central transaction table. It tracks all customer orders with their date, total amount, and current status. Use orderdate for time-based analysis and orderstatus for fulfillment tracking. Join with customers for customer details and order_items for line-item details.
