# BOM System Query Library
## Validated SQL Queries for Reuse and Reference

*Instructions for AI Agent*: 
- Search this library for queries matching user intent
- If similarity score > 0.85: Reuse the validated SQL with parameter substitution
- If similarity score 0.70-0.85: Adapt the SQL pattern for the new scenario
- If similarity score < 0.70: Generate new SQL using schema documentation
- Always verify parameters match expected types

---

## Query ID: WHERE_USED_001
### Where-Used Analysis (Find Parent Products Using a Component)

**User Intent**: Find which products/assemblies use a specific component
**Example Questions**: 
- "Which products use component IN-001?"
- "Where is this part used?"
- "Show me all assemblies containing batteries"
- "What BOMs have item X?"
- "Find parent assemblies for component Y"

**Validated SQL**:
```sql
SELECT DISTINCT 
  bd.parent_item_number,
  im.item_description as parent_description,
  bd.bom_id,
  bd.quantity,
  bd.is_active
FROM `{PROJECT}.{DATASET}.bom_details` bd
JOIN `{PROJECT}.{DATASET}.item_master` im 
  ON bd.parent_item_number = im.item_number
WHERE bd.component_item_number = @component_id
  AND bd.is_active = TRUE
ORDER BY bd.parent_item_number
LIMIT 100
```

**Parameters**:
- `@component_id` (STRING): Item number to search for (e.g., 'IN-001', 'BATTERY-001')

**Returns**: parent_item_number, parent_description, bom_id, quantity, is_active

**Usage Notes**:
- Use case-insensitive search if user provides category name instead of item_number
- For category search (e.g., "batteries"), join to item_master on component and filter by LOWER(category)
- Always filter is_active = TRUE for current BOMs

**Last Validated**: 2025-01-26
**Success Rate**: 100%
**Avg Execution Time**: <2 seconds


## Pattern 2: Component Explosion (What Goes Into This Product)

**Business Question**: "What components are in BOM EB-001?" OR "Show me the parts list" OR "Break down product assembly"

**SQL Pattern**:
```sql
SELECT 
  bd.component_item_number,
  im.item_description,
  im.category,
  bd.quantity,
  bd.quantity_unit,
  bd.supply_type,
  im.unit_cost,
  (bd.quantity * im.unit_cost) as extended_cost
FROM `{PROJECT}.{DATASET}.bom_details` bd
JOIN `{PROJECT}.{DATASET}.item_master` im 
  ON bd.component_item_number = im.item_number
WHERE bd.parent_item_number = @parent_id
  AND bd.is_active = TRUE
ORDER BY bd.sequence_number
```

**Keywords**: components in, parts list, BOM breakdown, what's in, product structure, explode BOM


## Pattern 3: Multi-Level BOM (Deep Structure with Recursion)

**Business Question**: "Show me all levels of the product structure" OR "Complete material list with sub-assemblies" OR "Full BOM tree"

**SQL Pattern**:
```sql
WITH RECURSIVE bom_tree AS (
  -- Level 0: Top level item
  SELECT 
    parent_item_number,
    component_item_number,
    quantity,
    0 as level,
    CAST(parent_item_number AS STRING) as path
  FROM `{PROJECT}.{DATASET}.bom_details`
  WHERE parent_item_number = @top_item
    AND is_active = TRUE
  
  UNION ALL
  
  -- Recursive: Get sub-components
  SELECT 
    bd.parent_item_number,
    bd.component_item_number,
    bd.quantity * bt.quantity as quantity,
    bt.level + 1,
    CONCAT(bt.path, ' > ', bd.parent_item_number)
  FROM `{PROJECT}.{DATASET}.bom_details` bd
  JOIN bom_tree bt ON bd.parent_item_number = bt.component_item_number
  WHERE bd.is_active = TRUE
    AND bt.level < 10  -- Prevent infinite loops
)
SELECT 
  level,
  component_item_number,
  im.item_description,
  im.category,
  quantity,
  path as structure_path
FROM bom_tree
JOIN `{PROJECT}.{DATASET}.item_master` im 
  ON bom_tree.component_item_number = im.item_number
ORDER BY path, level
```

**Keywords**: multi-level BOM, recursive BOM, full structure, all levels, indented BOM, complete tree


## Pattern 4: Cost Rollup Analysis

**Business Question**: "What's the total material cost for product EB-001?" OR "Calculate BOM cost" OR "Show cost breakdown by category"

**SQL Pattern**:
```sql
SELECT 
  bd.parent_item_number,
  parent.item_description,
  SUM(bd.quantity * comp.unit_cost) as total_material_cost,
  COUNT(DISTINCT bd.component_item_number) as component_count,
  STRING_AGG(DISTINCT comp.category ORDER BY comp.category) as categories_used
FROM `{PROJECT}.{DATASET}.bom_details` bd
JOIN `{PROJECT}.{DATASET}.item_master` comp 
  ON bd.component_item_number = comp.item_number
JOIN `{PROJECT}.{DATASET}.item_master` parent 
  ON bd.parent_item_number = parent.item_number
WHERE bd.parent_item_number = @parent_id
  AND bd.is_active = TRUE
GROUP BY bd.parent_item_number, parent.item_description
```

**Keywords**: cost rollup, total cost, material cost, price calculation, BOM costing, cost breakdown


## Pattern 5: Supply Chain Risk Analysis

**Business Question**: "Which BOMs have single-source components?" OR "Find supply chain risks" OR "Show items with long lead times from risky countries"

**SQL Pattern**:
```sql
SELECT 
  bd.parent_item_number,
  bd.component_item_number,
  im.item_description,
  im.supplier_code,
  im.country_of_origin,
  im.lead_time_days,
  bd.sourcing_type,
  CASE 
    WHEN bd.sourcing_type = 'SINGLE' AND im.lead_time_days > 30 THEN 'HIGH'
    WHEN bd.sourcing_type = 'SINGLE' THEN 'MEDIUM'
    WHEN im.lead_time_days > 60 THEN 'MEDIUM'
    ELSE 'LOW'
  END as risk_level
FROM `{PROJECT}.{DATASET}.bom_details` bd
JOIN `{PROJECT}.{DATASET}.item_master` im 
  ON bd.component_item_number = im.item_number
WHERE bd.is_active = TRUE
  AND (
    bd.sourcing_type = 'SINGLE' 
    OR im.lead_time_days > 30
    OR im.country_of_origin IN ('China', 'Taiwan')  -- Example risk countries
  )
ORDER BY risk_level DESC, im.lead_time_days DESC
```

**Keywords**: supply chain risk, single source, long lead time, supplier dependency, geopolitical risk


## Pattern 6: Obsolete Parts Detection

**Business Question**: "Are there obsolete parts still in active BOMs?" OR "Find discontinued components" OR "Show items needing redesign"

**SQL Pattern**:
```sql
SELECT 
  bd.parent_item_number,
  parent.item_description as parent_desc,
  bd.component_item_number,
  comp.item_description as component_desc,
  comp.status as component_status,
  comp.is_obsolete,
  bd.last_modified_date as bom_last_updated
FROM `{PROJECT}.{DATASET}.bom_details` bd
JOIN `{PROJECT}.{DATASET}.item_master` comp 
  ON bd.component_item_number = comp.item_number
JOIN `{PROJECT}.{DATASET}.item_master` parent 
  ON bd.parent_item_number = parent.item_number
WHERE bd.is_active = TRUE
  AND (comp.is_obsolete = TRUE OR comp.status = 'DISCONTINUED')
ORDER BY bd.parent_item_number, bd.component_item_number
```

**Keywords**: obsolete parts, discontinued components, phase-out, items needing replacement, redesign candidates


## Pattern 7: Supplier Consolidation Opportunity

**Business Question**: "Which suppliers provide the most components?" OR "Show supplier usage across BOMs" OR "Analyze vendor diversity"

**SQL Pattern**:
```sql
SELECT 
  im.supplier_code,
  COUNT(DISTINCT bd.component_item_number) as unique_components,
  COUNT(DISTINCT bd.parent_item_number) as products_served,
  SUM(bd.quantity * im.unit_cost) as total_spend,
  STRING_AGG(DISTINCT im.category ORDER BY im.category) as categories,
  AVG(im.lead_time_days) as avg_lead_time
FROM `{PROJECT}.{DATASET}.bom_details` bd
JOIN `{PROJECT}.{DATASET}.item_master` im 
  ON bd.component_item_number = im.item_number
WHERE bd.is_active = TRUE
  AND im.supplier_code IS NOT NULL
GROUP BY im.supplier_code
HAVING COUNT(DISTINCT bd.component_item_number) >= 3
ORDER BY total_spend DESC
LIMIT 20
```

**Keywords**: supplier consolidation, vendor analysis, spend analysis, supplier usage, procurement optimization


## Pattern 8: Make vs Buy Analysis

**Business Question**: "What components are manufactured vs purchased?" OR "Show make/buy split" OR "Which items should we make internally?"

**SQL Pattern**:
```sql
SELECT 
  bd.supply_type,
  COUNT(DISTINCT bd.component_item_number) as component_count,
  SUM(bd.quantity * im.unit_cost) as total_value,
  AVG(im.lead_time_days) as avg_lead_time,
  STRING_AGG(DISTINCT im.category ORDER BY im.category LIMIT 5) as top_categories
FROM `{PROJECT}.{DATASET}.bom_details` bd
JOIN `{PROJECT}.{DATASET}.item_master` im 
  ON bd.component_item_number = im.item_number
WHERE bd.is_active = TRUE
GROUP BY bd.supply_type
ORDER BY total_value DESC
```

**Keywords**: make vs buy, manufactured vs purchased, supply type, internal vs external, procurement strategy


## Pattern 9: New Product Introduction (NPI) Impact

**Business Question**: "Which BOMs use NPI components?" OR "Show products with design-phase parts" OR "Find items not yet in production"

**SQL Pattern**:
```sql
SELECT 
  bd.parent_item_number,
  parent.item_description as product,
  bd.component_item_number,
  comp.item_description as npi_component,
  comp.status,
  bd.quantity,
  im_cost.unit_cost * bd.quantity as extended_cost
FROM `{PROJECT}.{DATASET}.bom_details` bd
JOIN `{PROJECT}.{DATASET}.item_master` comp 
  ON bd.component_item_number = comp.item_number
JOIN `{PROJECT}.{DATASET}.item_master` parent 
  ON bd.parent_item_number = parent.item_number
LEFT JOIN `{PROJECT}.{DATASET}.item_master` im_cost 
  ON bd.component_item_number = im_cost.item_number
WHERE bd.is_active = TRUE
  AND comp.is_npi = TRUE
ORDER BY bd.parent_item_number, bd.component_item_number
```

**Keywords**: NPI components, new product introduction, design phase, not yet released, under development


## Pattern 10: Compliance and Certification Check

**Business Question**: "Which components need ROHS compliance?" OR "Show parts with environmental certifications" OR "Find items without REACH compliance"

**SQL Pattern**:
```sql
SELECT 
  bd.parent_item_number,
  bd.component_item_number,
  im.item_description,
  im.compliance_status,
  im.country_of_origin,
  im.material,
  CASE 
    WHEN im.compliance_status LIKE '%ROHS%' AND im.compliance_status LIKE '%REACH%' THEN 'FULLY_COMPLIANT'
    WHEN im.compliance_status LIKE '%ROHS%' OR im.compliance_status LIKE '%REACH%' THEN 'PARTIAL'
    ELSE 'NON_COMPLIANT'
  END as compliance_level
FROM `{PROJECT}.{DATASET}.bom_details` bd
JOIN `{PROJECT}.{DATASET}.item_master` im 
  ON bd.component_item_number = im.item_number
WHERE bd.is_active = TRUE
ORDER BY compliance_level, bd.parent_item_number
```

**Keywords**: compliance check, ROHS, REACH, certification, environmental, regulatory, standards


## Pattern 11: Phantom Assembly Handling

**Business Question**: "Show me phantom assemblies" OR "Which sub-assemblies pass through without inventory?" OR "Find transient components"

**SQL Pattern**:
```sql
SELECT 
  bd.parent_item_number,
  bd.component_item_number,
  im.item_description,
  im.item_type,
  bd.quantity,
  bd.is_phantom,
  bd.supply_type
FROM `{PROJECT}.{DATASET}.bom_details` bd
JOIN `{PROJECT}.{DATASET}.item_master` im 
  ON bd.component_item_number = im.item_number
WHERE bd.is_active = TRUE
  AND bd.is_phantom = TRUE
ORDER BY bd.parent_item_number
```

**Keywords**: phantom assembly, transient component, pass-through, no inventory, intermediate assembly


## Pattern 12: Optional Component Configuration

**Business Question**: "What are the configurable options for product EB-001?" OR "Show optional components" OR "Which parts are customer-selectable?"

**SQL Pattern**:
```sql
SELECT 
  bd.parent_item_number,
  bd.component_item_number,
  im.item_description,
  im.category,
  bd.quantity,
  im.unit_cost,
  bd.is_optional,
  bd.notes as option_notes
FROM `{PROJECT}.{DATASET}.bom_details` bd
JOIN `{PROJECT}.{DATASET}.item_master` im 
  ON bd.component_item_number = im.item_number
WHERE bd.parent_item_number = @parent_id
  AND bd.is_active = TRUE
  AND bd.is_optional = TRUE
ORDER BY im.category, bd.component_item_number
```

**Keywords**: optional components, configurable, customer options, variants, selectable parts


## Common Query Modifiers and Filters

### Date Range Filters (for time-based analysis):
```sql
WHERE bd.effective_date <= CURRENT_DATE()
  AND (bd.expiration_date IS NULL OR bd.expiration_date >= CURRENT_DATE())
```

### Active Items Only:
```sql
WHERE bd.is_active = TRUE 
  AND im.status = 'ACTIVE'
```

### Case-Insensitive Search Pattern:
```sql
WHERE LOWER(im.category) IN UNNEST(@terms_lower)
  OR REGEXP_CONTAINS(im.category, r'(?i)\b(term1|term2)\b')
```

### Cost Threshold:
```sql
HAVING SUM(bd.quantity * im.unit_cost) > @min_cost
```

## Query Complexity Levels

**Level 1 (Simple)**: Single table, basic filters
- "Show all active components"
- "List items by category"

**Level 2 (Moderate)**: One join, aggregation
- "What components are in this BOM?"
- "Count items by supplier"

**Level 3 (Complex)**: Multiple joins, grouping, calculations
- "Calculate total BOM cost with breakdown"
- "Find supply chain risks"

**Level 4 (Advanced)**: Recursive CTEs, window functions, multi-level analysis
- "Multi-level BOM explosion"
- "Cost rollup through assembly hierarchy"

## Tips for Query Construction

1. **Always use parameterized queries** for user inputs: `@component_id`, `@parent_id`, `@terms_lower`
2. **Filter early**: Apply `is_active = TRUE` and date ranges in WHERE clauses
3. **Use LIMIT**: Cap results at 100 unless explicitly requested
4. **Project only needed columns**: Avoid `SELECT *`
5. **Leverage partitioning**: Use `effective_date` or `created_date` in filters
6. **Case-insensitive matching**: Use `LOWER()` and `REGEXP_CONTAINS` for text searches

