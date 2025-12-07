# order_items

Order line items table containing individual products within each order.

## Table Details

- **Database**: athena_db
- **Catalog**: AwsDataCatalog
- **Location**: s3://athena-datasource-cg/order_items

## Columns

| Column | Type | Description |
|--------|------|-------------|
| orderitemid | string | Unique identifier for the order item (Primary Key) |
| orderid | string | Reference to the parent order (Foreign Key → orders.orderid) |
| productid | string | Reference to the product (Foreign Key → products.productid) |
| quantity | string | Number of units ordered (should be cast to INT for calculations) |
| unitprice | string | Price per unit at time of order (should be cast to DOUBLE for calculations) |

## Common Queries

- Get items for an order: `SELECT * FROM order_items WHERE orderid = 'xxx'`
- Get item with product details: `SELECT oi.*, p.productname, p.category FROM order_items oi JOIN products p ON oi.productid = p.productid WHERE oi.orderid = 'xxx'`
- Calculate line total: `SELECT orderitemid, CAST(quantity AS INT) * CAST(unitprice AS DOUBLE) as line_total FROM order_items`
- Top selling products: `SELECT productid, SUM(CAST(quantity AS INT)) as total_sold FROM order_items GROUP BY productid ORDER BY total_sold DESC`

## Relationships

- **orders**: order_items.orderid → orders.orderid (Many to One)
- **products**: order_items.productid → products.productid (Many to One)
- Each order item belongs to one order and references one product

## Business Context

The order_items table stores the individual line items for each order. It links orders to products and captures the quantity and price at the time of purchase. Use this table for product sales analysis, revenue calculations, and basket analysis. Remember to cast quantity and unitprice to numeric types for calculations.
