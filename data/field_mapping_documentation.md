# BOM System Field Mapping Documentation

## Table 1: item_master

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| item_number | STRING | Unique identifier for the item/component. Also known as part number, SKU, or material code. Used to reference items across BOMs. |
| item_description | STRING | Detailed description of the item. Contains searchable text about what the item is, including common names, models, and specifications. |
| item_type | STRING | Classification level in product hierarchy (RAW_MATERIAL, COMPONENT, ASSEMBLY, FINISHED_GOOD). Use to filter by manufacturing stage or procurement strategy. |
| category | STRING | Business/functional grouping of items. Examples: ELECTRONICS (batteries, circuits, memory), MECHANICAL (fasteners, housings), SOFTWARE. Search here for items by technology domain or product family. |
| uom | STRING | Unit of measure - how items are counted or measured (EA=each/pieces, KG=kilograms, M=meters, L=liters). Important for quantity calculations and ordering. |
| weight | NUMERIC | Physical weight of a single unit. Use with uom to calculate shipping weight or material handling requirements. |
| dimensions | STRING | Physical size in format LxWxH (length × width × height). Used for packaging, storage, and shipping planning. |
| color | STRING | Visual appearance or color code. Relevant for consumer-facing products, aesthetic requirements, or visual identification during assembly. |
| material | STRING | What the item is made of (plastic, aluminum, steel, silicon, etc.). Important for material compliance, recycling, and compatibility checks. |
| manufacturer | STRING | Company that originally designs/produces the item. Different from supplier who sells it. Used for quality traceability and warranty claims. |
| manufacturer_part_number | STRING | OEM part number assigned by the manufacturer. Use this to cross-reference with manufacturer catalogs or find exact replacement parts. |
| supplier_code | STRING | Vendor ID or supplier identifier in procurement system. Links to who you buy from, not who makes it. Query this to analyze supplier performance or consolidation. |
| supplier_part_number | STRING | Vendor's catalog number for ordering. May differ from manufacturer part number. Use for purchase orders and supplier communications. |
| lead_time_days | INTEGER | How many days from order to delivery. Critical for production planning, inventory calculations, and supply chain risk assessment. |
| minimum_order_quantity | NUMERIC | Smallest quantity that can be ordered at once (MOQ). Affects inventory strategy and cost analysis. |
| unit_cost | NUMERIC | Price per unit in specified currency. Use for cost rollup calculations, price variance analysis, and budget planning. |
| currency | STRING | Which currency the unit_cost is expressed in (USD, EUR, JPY, etc.). Important for multi-currency cost reporting and forex impact analysis. |
| country_of_origin | STRING | Where the item is manufactured. Relevant for trade compliance, tariffs, duties, and supply chain risk (geopolitical). |
| compliance_status | STRING | Environmental and safety certifications (ROHS=lead-free, REACH=chemical restrictions, etc.). Query to ensure regulatory compliance for target markets. |
| is_serialized | BOOLEAN | True if each unit needs unique serial number tracking. Important for warranty, recalls, and traceability of high-value or regulated items. |
| is_npi | BOOLEAN | New Product Introduction flag - indicates items in design/ramp phase. Use to identify items not yet in mass production or under evaluation. |
| is_obsolete | BOOLEAN | True if item is being phased out or discontinued. Query to find items needing redesign, last-time-buy, or replacement sourcing. |
| status | STRING | Lifecycle state (ACTIVE=in use, INACTIVE=not currently used, DISCONTINUED=no longer available). Filter active items for current BOMs. |
| created_date | DATE | Item creation date |
| last_modified_date | DATE | Last modification date |
| revision | STRING | Current revision number |
| notes | STRING | Additional notes and comments |

## Table 2: bom_details

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| bom_id | STRING | Unique identifier for this bill of materials. One parent item can have multiple BOM versions (revisions, alternates). |
| parent_item_number | STRING | The finished assembly or product that uses these components. References item_master.item_number. Query this to find what components go into a product. |
| component_item_number | STRING | The part or material used in the assembly. References item_master.item_number. Query this to find which BOMs/products use a specific component. |
| quantity | NUMERIC | How many units of the component are needed per unit of parent. Used for material planning, cost rollup, and consumption calculations. |
| quantity_unit | STRING | Unit of measure for the quantity (EA, KG, M). Must align with component item's uom for proper material calculations. |
| sequence_number | INTEGER | Order of assembly or installation steps. Use to generate work instructions or identify position in product structure. |
| supply_type | STRING | How component is obtained (MAKE=manufactured internally, BUY=purchased, ASSEMBLE=sub-assembly). Query for make-vs-buy analysis or capacity planning. |
| sourcing_type | STRING | Supply chain strategy (SINGLE=one supplier, DUAL=two suppliers, MULTI=multiple suppliers). Important for risk analysis and supplier diversity. |
| supplier_code | STRING | Preferred vendor for this specific component in this BOM. May override item_master default supplier. Use for supplier-specific sourcing decisions. |
| supplier_part_number | STRING | Vendor's catalog number for this component. Specific to this BOM line, may differ from item master. |
| lead_time_days | INTEGER | How long to get this component for this BOM (days). May differ from item_master lead time based on supplier or volume. Critical for MRP and production scheduling. |
| effective_date | DATE | When this BOM version becomes valid. Use to find BOMs active during a specific time period or for engineering change tracking. |
| expiration_date | DATE | When this BOM version is no longer valid. NULL means currently effective. Query to find BOMs that were active in the past or will activate in future. |
| is_active | BOOLEAN | Whether this BOM line is currently in use. False means component was removed but record kept for history. Filter true for current production BOMs. |
| is_optional | BOOLEAN | True if component is optional or customer-configurable. Relevant for product variants, options, and configure-to-order scenarios. |
| is_phantom | BOOLEAN | True if component exists only in planning (intermediate sub-assembly). Phantom items pass through without inventory. Important for MRP and costing logic. |
| scrap_factor | NUMERIC | Expected waste percentage (e.g., 0.05 = 5% scrap). Used to calculate actual material needed = quantity × (1 + scrap_factor). |
| yield_factor | NUMERIC | Manufacturing success rate (e.g., 0.95 = 95% good units). Inverse of scrap. Used for realistic material and capacity planning. |
| setup_time_minutes | INTEGER | Machine/workstation preparation time before production starts. One-time cost per batch. Used for capacity planning and batch size optimization. |
| cycle_time_minutes | INTEGER | Time to produce one unit once setup is complete. Multiplied by quantity for total production time. Critical for throughput and capacity analysis. |
| labor_hours | NUMERIC | Human effort hours needed per unit of parent. Used for labor cost rollup, staffing requirements, and productivity analysis. |
| tooling_required | STRING | Specialized equipment, jigs, fixtures, or molds needed. Important for capital planning, tooling availability checks, and setup preparation. |
| special_instructions | STRING | Assembly notes, precautions, or techniques. Contains searchable text for "how to build" knowledge. Query for critical assembly guidance. |
| quality_requirements | STRING | Inspection criteria, tolerances, or acceptance standards. Use to identify items with strict quality controls or certification needs. |
| test_requirements | STRING | What tests must be performed (electrical, mechanical, functional). Query to identify testing bottlenecks or certification requirements. |
| packaging_requirements | STRING | How component must be protected or prepared for assembly. Relevant for fragile items, ESD-sensitive parts, or special handling. |
| created_by | STRING | User ID or name of person who created this BOM record. Use for audit trails, change attribution, or engineering ownership. |
| created_date | DATE | When this BOM record was first entered. Use for BOM age analysis, change frequency tracking, or historical queries. |
| last_modified_by | STRING | User who most recently changed this BOM. Important for accountability, change management, and engineering coordination. |
| last_modified_date | DATE | Most recent update timestamp. Query to find recently changed BOMs, track change velocity, or identify stale records. |
| revision | STRING | Engineering revision or version number (A, B, 1.0, 2.5, etc.). Use to track BOM evolution, compare revisions, or enforce revision control. |
| approval_status | STRING | Workflow state (DRAFT=work in progress, PENDING=awaiting approval, APPROVED=released for production). Filter APPROVED for production-ready BOMs. |
| notes | STRING | Free-text comments about this BOM line. Contains searchable context like "replaces old part", "critical for Q1 launch", etc. |

## Relationships (ODW - No Foreign Keys)

- **Logical Primary Key**: `item_master.item_number`
- **Logical Primary Key**: `bom_details.bom_id` (composite with parent_item_number, component_item_number)
- **Logical Relationship**: `bom_details.parent_item_number` → `item_master.item_number`
- **Logical Relationship**: `bom_details.component_item_number` → `item_master.item_number`

**Note**: In Operational Data Warehouses (ODW), foreign key constraints are typically not defined for:
- **Performance**: Avoids constraint checking overhead during bulk loads
- **Flexibility**: Allows for data loading from multiple sources
- **Scalability**: Better performance with large datasets

## BigQuery Optimization

### Partitioning
- `item_master`: Partitioned by `created_date`
- `bom_details`: Partitioned by `effective_date`

### Clustering
- `item_master`: Clustered by `item_type`, `category`, `status`
- `bom_details`: Clustered by `parent_item_number`, `bom_id`, `is_active`

### Recommended Queries
```sql
-- Use partitioning columns in WHERE clauses
SELECT * FROM item_master 
WHERE created_date >= '2024-01-01'

-- Use clustering columns for better performance
SELECT * FROM bom_details 
WHERE parent_item_number = 'EB-001' 
AND is_active = TRUE
```
