-- =========================================================
-- bom-ai-demo : BigQuery schema and data for AI Agent PoC
-- =========================================================

-- 1️⃣ Create dataset (run only once)
-- Note: Replace <YOUR_PROJECT_ID> with your actual GCP project ID
-- This will be automatically replaced by the Python script
CREATE SCHEMA IF NOT EXISTS `<YOUR_PROJECT_ID>.bom_demo`
OPTIONS(location = 'us-central1');

-- 2️⃣ Drop existing tables
DROP TABLE IF EXISTS `<YOUR_PROJECT_ID>.bom_demo.product_master`;
DROP TABLE IF EXISTS `<YOUR_PROJECT_ID>.bom_demo.bom_component_map`;

-- 3️⃣ Create Product Master
CREATE TABLE `<YOUR_PROJECT_ID>.bom_demo.product_master` (
  product_id STRING,
  product_name STRING,
  category STRING,
  is_serialized BOOL,
  is_npi BOOL,
  status STRING,
  country_of_origin STRING,
  last_updated DATE
);

-- 4️⃣ Create BOM Component Map
CREATE TABLE `<YOUR_PROJECT_ID>.bom_demo.bom_component_map` (
  bom_id STRING,
  assembly_id STRING,
  component_id STRING,
  quantity NUMERIC,
  effective_date DATE,
  is_active BOOL
);

-- 5️⃣ Sample Data
INSERT INTO `<YOUR_PROJECT_ID>.bom_demo.product_master` VALUES
('P1001', 'Electric Bike', 'ASSEMBLY', FALSE, FALSE, 'ACTIVE', 'USA', '2025-01-01'),
('P1002', 'Smart Scooter', 'ASSEMBLY', FALSE, FALSE, 'ACTIVE', 'Germany', '2025-02-01'),
('P2001', 'Lithium Battery', 'BATTERY', FALSE, TRUE, 'ACTIVE', 'China', '2025-01-10'),
('P2002', 'Motor Controller', 'ELECTRONICS', TRUE, FALSE, 'ACTIVE', 'Vietnam', '2025-02-01'),
('P2003', 'Aluminum Frame', 'FRAME', FALSE, FALSE, 'ACTIVE', 'USA', '2025-03-01'),
('P2004', 'Display Panel', 'DISPLAY', TRUE, TRUE, 'OBSOLETE', 'Vietnam', '2024-12-01'),
('P3001', 'Memory Module', 'MEMORY', FALSE, TRUE, 'ACTIVE', 'Korea', '2025-03-15'),
('P3002', 'Hard Drive', 'STORAGE', FALSE, FALSE, 'ACTIVE', 'Malaysia', '2025-03-10');

INSERT INTO `<YOUR_PROJECT_ID>.bom_demo.bom_component_map` VALUES
('BOM1001', 'P1001', 'P2001', 1, '2025-01-01', TRUE),
('BOM1001', 'P1001', 'P2002', 1, '2025-01-01', TRUE),
('BOM1001', 'P1001', 'P2003', 1, '2025-01-01', TRUE),
('BOM1001', 'P1001', 'P2004', 1, '2025-02-01', TRUE),
('BOM2001', 'P1002', 'P2001', 1, '2025-02-01', TRUE),
('BOM2001', 'P1002', 'P3001', 1, '2025-02-10', TRUE),
('BOM2001', 'P1002', 'P3002', 1, '2025-03-01', TRUE);
