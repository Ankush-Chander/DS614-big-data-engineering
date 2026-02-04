---
delivery date:
  - "[[2026-02-04]]"
  - "[[2026-02-05]]"
---

# OLTP vs OLAP

| Property | Transaction processing systems (OLTP) | Analytic systems (OLAP) |
| --- | --- | --- |
| Main read pattern | Small number of records per query, fetched by key | Aggregate over large number of records |
| Main write pattern | Random-access, low-latency writes from user input | Bulk import (ETL) or event stream |
| Primarily used by | End user/customer, via web application | Internal analyst, for decision support |
| What data represents | Latest state of data (current point in time) | History of events that happened over time |
| Dataset size | Gigabytes to terabytes | Terabytes to petabytes |

# Data Warehouse
A data warehouse, is a separate database that analysts can query without affecting OLTP operations. The data warehouse contains a read-only copy of the data in all the various OLTP systems in the company.


# Columnar Storage
## Row vs. Column

**Row-Oriented**: Stores all data for a single record (e.g., Name, Age, Salary) together. This is ideal for OLTP (Online Transaction Processing) where you frequently read or write specific individual records (e.g., adding a new user).   

**Column-Oriented**: Stores all data for a single attribute (e.g., all "Salaries") together. This is ideal for OLAP (Online Analytical Processing) where you want to perform calculations on a specific metric across millions of records (e.g., "What is the average salary?").


Let's consider a simple `Employees` table with the following schema:
`id` (int), `age` (int), `salary` (int), `dept` (string)

| id | age | salary | dept |
|----|-----|--------|------|
| 0 | 25 | 50000 | HR |
| 1 | 30 | 60000 | Tech |
| 2 | 45 | 90000 | Sales |

#### 1. Row-Oriented Storage
In a row store, data is written **row by row**. The storage on disk looks like a long continuous stream of records:

`0, 25, 50000, HR; 1, 30, 60000, Tech; 2, 45, 90000, Sales`

If you want to calculate the **Average Salary**:  
- The generic "Row" engine must read the entire row (including `id`, `age`, and `dept`) just to get to the `salary`.   
- This wastes I/O bandwidth reading data you don't need.

#### 2. Column-Oriented Storage
In a column store, data is written **column by column**.

`0, 1, 2` (IDs)
`25, 30, 45` (Ages)
`50000, 60000, 90000` (Salaries)
`HR, Tech, Sales` (Depts)

If you want to calculate the **Average Salary**:
- The engine only reads the `Salaries` block: `50000, 60000, 90000`.  
- It ignores `IDs`, `Ages`, and `Depts` entirely.  
- This is significantly faster for aggregations (OLAP).  

## Why Columnar Storage is better for OLAP

1. **I/O Efficiency**: When performing an aggregation, you only need to read the columns that are relevant to the query. This reduces the amount of data that needs to be read from disk. 
2. **Compression**: Since all data in a column is of the same type, it can be compressed much more effectively than row-oriented storage. 
3. **Cache Efficiency**: Since related data is stored together, it is more likely to be found in the CPU cache, which reduces the time it takes to access the data. 
