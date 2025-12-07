# products

Product catalog table containing product information and inventory.

## Table Details

- **Database**: athena_db
- **Catalog**: AwsDataCatalog
- **Location**: s3://athena-datasource-cg/products

## Columns

| Column | Type | Description |
|--------|------|-------------|
| productid | string | Unique identifier for the product (Primary Key) |
| productname | string | Name of the product |
| category | string | Product category (e.g., 'Electronics', 'Clothing', 'Home', etc.) |
| price | string | Current price of the product (should be cast to DOUBLE for calculations) |
| stockquantity | string | Current inventory level (should be cast to INT for calculations) |

## Common Queries

- Get product by ID: `SELECT * FROM products WHERE productid = 'xxx'`
- Get products by category: `SELECT * FROM products WHERE category = 'Electronics'`
- Get low stock products: `SELECT * FROM products WHERE CAST(stockquantity AS INT) < 10`
- Products by price range: `SELECT * FROM products WHERE CAST(price AS DOUBLE) BETWEEN 10 AND 100`
- Category summary: `SELECT category, COUNT(*) as product_count, AVG(CAST(price AS DOUBLE)) as avg_price FROM products GROUP BY category`

## Relationships

- **order_items**: products.productid → order_items.productid (One to Many)
- A product can appear in multiple order items across different orders

## Business Context

The products table is the product master data. It contains the product catalog with current pricing and inventory levels. Use this for product lookups, category analysis, and inventory management. Join with order_items to analyze product sales performance.
