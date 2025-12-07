# Schema Overview

E-commerce database with customer orders and product catalog.

## Tables

### customers
Customer profiles and contact information.
- customerid (PK), firstname, lastname, email, phonenumber

### orders
Order transactions and status tracking.
- orderid (PK), customerid (FK → customers), orderdate, orderamount, orderstatus

### order_items
Line items within each order.
- orderitemid (PK), orderid (FK → orders), productid (FK → products), quantity, unitprice

### products
Product catalog with pricing and inventory.
- productid (PK), productname, category, price, stockquantity

## Relationships

```
customers (1) ──── (N) orders (1) ──── (N) order_items (N) ──── (1) products
```

## Common Analysis Patterns

### Sales Analysis
```sql
SELECT 
    p.category,
    COUNT(DISTINCT o.orderid) as order_count,
    SUM(CAST(oi.quantity AS INT)) as units_sold,
    SUM(CAST(oi.quantity AS INT) * CAST(oi.unitprice AS DOUBLE)) as revenue
FROM orders o
JOIN order_items oi ON o.orderid = oi.orderid
JOIN products p ON oi.productid = p.productid
GROUP BY p.category
```

### Customer Orders
```sql
SELECT 
    c.firstname, c.lastname, c.email,
    COUNT(o.orderid) as total_orders,
    SUM(CAST(o.orderamount AS DOUBLE)) as total_spent
FROM customers c
LEFT JOIN orders o ON c.customerid = o.customerid
GROUP BY c.customerid, c.firstname, c.lastname, c.email
```

### Order Details
```sql
SELECT 
    o.orderid, o.orderdate, o.orderstatus,
    c.firstname, c.lastname,
    p.productname, oi.quantity, oi.unitprice
FROM orders o
JOIN customers c ON o.customerid = c.customerid
JOIN order_items oi ON o.orderid = oi.orderid
JOIN products p ON oi.productid = p.productid
```

## Important Notes

- All columns are STRING type in Athena - cast to appropriate types for calculations
- Use CAST(column AS INT) for integers
- Use CAST(column AS DOUBLE) for decimals
- Date format in orderdate is typically YYYY-MM-DD
