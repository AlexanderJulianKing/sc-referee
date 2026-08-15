## Data Description

This dataset contains responses from a customer satisfaction survey conducted across three product categories on an e-commerce platform.

**Format:** CSV with headers
**Records:** 20 customer responses
**Columns:**
- `customer_id`: Sequential customer identifier (1-20)
- `category`: Product category (Electronics, Fashion, Home)
- `satisfaction`: Ordinal satisfaction rating (Low, Medium, High)

**Data characteristics:**
- Cross-tabulated categorical data
- No missing values
- Each row represents one customer's response
- Satisfaction responses distributed across three categories with varying proportions

The data structure is designed for chi-square test of independence, enabling statistical evaluation of whether customer satisfaction differs significantly across product categories and quantification of association strength via Cramér's V effect size.