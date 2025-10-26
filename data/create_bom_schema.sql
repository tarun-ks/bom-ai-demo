-- =========================================================
-- bom-ai-demo : BigQuery schema and data for AI Agent PoC
-- Comprehensive BOM System with Realistic Manufacturing Data
-- =========================================================

-- 1️⃣ Create dataset (run only once)
-- Note: Replace <YOUR_PROJECT_ID> with your actual GCP project ID
-- This will be automatically replaced by the Python script
CREATE SCHEMA IF NOT EXISTS `<YOUR_PROJECT_ID>.bom_demo`
OPTIONS(location = 'us-central1');

-- 2️⃣ Drop existing tables
DROP TABLE IF EXISTS `<YOUR_PROJECT_ID>.bom_demo.item_master`;
DROP TABLE IF EXISTS `<YOUR_PROJECT_ID>.bom_demo.bom_details`;

-- 3️⃣ Create Item Master Table (ODW - No Foreign Keys)
-- Note: In data warehouses, FK constraints are typically not defined for performance
CREATE TABLE `<YOUR_PROJECT_ID>.bom_demo.item_master` (
  item_number STRING,
  item_description STRING,
  item_type STRING,
  category STRING,
  uom STRING,
  weight NUMERIC,
  dimensions STRING,
  color STRING,
  material STRING,
  manufacturer STRING,
  manufacturer_part_number STRING,
  supplier_code STRING,
  supplier_part_number STRING,
  lead_time_days INT64,
  minimum_order_quantity NUMERIC,
  unit_cost NUMERIC,
  currency STRING,
  country_of_origin STRING,
  compliance_status STRING,
  is_serialized BOOL,
  is_npi BOOL,
  is_obsolete BOOL,
  status STRING,
  created_date DATE,
  last_modified_date DATE,
  revision STRING,
  notes STRING
)
PARTITION BY created_date
CLUSTER BY item_type, category, status;

-- 4️⃣ Create BOM Details Table (ODW - No Foreign Keys)
-- Note: Relationships are maintained through data integrity, not FK constraints
CREATE TABLE `<YOUR_PROJECT_ID>.bom_demo.bom_details` (
  bom_id STRING,
  parent_item_number STRING,
  component_item_number STRING,
  quantity NUMERIC,
  quantity_unit STRING,
  sequence_number INT64,
  supply_type STRING,
  sourcing_type STRING,
  supplier_code STRING,
  supplier_part_number STRING,
  lead_time_days INT64,
  effective_date DATE,
  expiration_date DATE,
  is_active BOOL,
  is_optional BOOL,
  is_phantom BOOL,
  scrap_factor NUMERIC,
  yield_factor NUMERIC,
  setup_time_minutes INT64,
  cycle_time_minutes INT64,
  labor_hours NUMERIC,
  tooling_required STRING,
  special_instructions STRING,
  quality_requirements STRING,
  test_requirements STRING,
  packaging_requirements STRING,
  created_by STRING,
  created_date DATE,
  last_modified_by STRING,
  last_modified_date DATE,
  revision STRING,
  approval_status STRING,
  notes STRING
)
PARTITION BY effective_date
CLUSTER BY parent_item_number, bom_id, is_active;

