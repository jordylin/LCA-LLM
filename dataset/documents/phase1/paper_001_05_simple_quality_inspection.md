# Quality Inspection Report for Selective Laser Melting of 316L Stainless Steel Flat Washers

**Report Number:** QIR-SLM-316L-2023-08-015  
**Date of Inspection:** October 26, 2023  
**Inspector:** J. Rodriguez, Senior Quality Engineer  
**Process Evaluated:** Selective Laser Melting (SLM) Batch #B-2847  
**Product:** 316L Stainless Steel Flat Washers, Lot #W-3377  

---

## 1.0 Executive Summary

This report documents the quality inspection for manufacturing lot #W-3377 comprising thirty-three (33) 316L stainless steel flat washers produced via Selective Laser Melting. The inspection was conducted in accordance with internal quality procedure QP-AM-04 and references ASTM F3184-16 for additive manufacturing of metal components. All dimensional, material, and process parameters met specified requirements. The manufacturing batch demonstrated acceptable process control with proper documentation of material inputs, energy consumption, and waste streams.

**Overall Finding:** **PASS** - All inspected characteristics conform to established specifications.

---

## 2.0 Inspection Scope and Methodology

### 2.1 Inspection Objectives

This inspection verified:
- Conformance of finished washers to dimensional specifications
- Proper documentation of material consumption and process parameters
- Effective management of process by-products and recycling streams
- Adherence to established manufacturing procedures

### 2.2 Inspection Methods

- **Dimensional Verification:** Coordinate Measuring Machine (CMM) with 0.001 mm resolution
- **Visual Inspection:** 10x magnification per ASTM F3122 guidelines
- **Material Traceability:** Verification of material certificates and batch tracking
- **Process Documentation:** Review of machine logs and operator records
- **Mass Verification:** Precision balance with 0.01 g accuracy

---

## 3.0 Material and Process Verification

### 3.1 Raw Material Consumption

All materials used in the manufacturing process were verified against certified specifications and properly documented in the material traceability system.

| Material Description | Specification | Quantity | Certification Verified |
|---------------------|----------------|----------|------------------------|
| X2CrNiMo1712 stainless steel for powder atomization (316L base material) | AMS 5688 | 4.11 kg | Yes - Cert #M-22841 |
| Process water for water atomization | ASTM D1193 Type IV | 16.8 kg | Yes - Lab Report #W-7742 |

*Note: Water quality parameters (conductivity, TOC) were within specification limits per internal testing.*

### 3.2 Process Gases

Shielding and processing gases were supplied per established procedures with continuous monitoring of purity levels.

| Gas Type | Purity Specification | Quantity | Delivery System |
|----------|---------------------|----------|----------------|
| Argon shielding and processing gas | 99.998% minimum | 3.08 kg | Bulk supply with in-line purification |

**Process Context:** The argon consumption reflects standard operating parameters including chamber purging (700 L initial fill) and continuous flow during processing (54 L per component). Gas purity was maintained above 99.998% throughout the build cycle.

### 3.3 Energy Consumption

Electrical energy consumption was monitored and recorded through the facility's power monitoring system.

| Process Stage | Energy Consumption | Equipment | Monitoring Method |
|---------------|-------------------|-----------|------------------|
| Water atomization of 316L powder | 2.55 kWh | Atomization system #A-7 | Direct meter reading |
| Selective Laser Melting process | 64.92 kWh | SLM 280HL System #AM-12 | Integrated power monitor |

**Historical Comparison:** Previous similar batch (Lot #W-3312, June 2023) showed SLM energy consumption of 67.4 kWh, representing a 3.7% improvement in energy efficiency for the current lot.

**Process Context:** The SLM system operated for 13.38 hours with nominal power consumption of 5.5 kW during laser operation and 3.5 kW during non-processing periods. The water atomization energy intensity was calculated at 2.23 MJ/kg of powder produced.

---

## 4.0 Product Quality Assessment

### 4.1 Finished Product Specifications

| Characteristic | Specification | Actual (Average) | Tolerance | Conformance |
|----------------|---------------|------------------|-----------|-------------|
| Total mass of finished washers | 0.61 kg | 0.61 kg | ±0.01 kg | PASS |
| Quantity produced | 33 units | 33 units | Exact count | PASS |
| Outer diameter | 20.0 mm | 20.01 mm | ±0.05 mm | PASS |
| Inner diameter | 10.5 mm | 10.49 mm | ±0.05 mm | PASS |
| Thickness | 2.0 mm | 2.01 mm | ±0.03 mm | PASS |
| Surface roughness (Ra) | ≤10 μm | 8.2 μm | - | PASS |

### 4.2 Dimensional Verification Results

All thirty-three washers underwent 100% dimensional inspection using CMM. The results demonstrated excellent dimensional stability and repeatability across the entire build plate.

**Sample Measurements (5 of 33 washers):**

| Washer ID | Outer Diameter (mm) | Inner Diameter (mm) | Thickness (mm) | Flatness (mm) |
|-----------|---------------------|---------------------|----------------|---------------|
| W-3377-01 | 20.012 | 10.492 | 2.008 | 0.008 |
| W-3377-08 | 20.009 | 10.488 | 2.013 | 0.006 |
| W-3377-15 | 20.015 | 10.491 | 2.011 | 0.009 |
| W-3377-22 | 20.008 | 10.493 | 2.009 | 0.007 |
| W-3377-29 | 20.011 | 10.489 | 2.012 | 0.005 |

*All measurements within specified tolerances. Maximum deviation from nominal: 0.015 mm.*

### 4.3 Visual and Surface Inspection

Visual examination under 10x magnification revealed consistent surface finish with no evidence of:
- Unfused powder particles
- Surface cracking or delamination
- Significant porosity
- Discoloration or oxidation

The as-built surface exhibited characteristic SLM texture with uniform bead appearance. No post-processing (e.g., machining, blasting) was performed prior to inspection.

---

## 5.0 By-Product Management and Material Recovery

### 5.1 Material Recovery Streams

The manufacturing process incorporates established procedures for material recovery and reuse to optimize resource utilization.

| Material Stream | Quantity | Handling Procedure | Destination |
|----------------|----------|-------------------|-------------|
| 316L powder reused within SLM process | 2.94 kg | Sieved and blended with virgin powder | Returned to SLM powder feed system |
| 316L powder returned for remelting | 0.15 kg | Collected in dedicated containers | Sent to water atomization facility |
| Recovered process water from water atomization | 16.4 kg | Filtration and treatment | Returned to process water system |

**Process Note:** The powder reuse rate of approximately 71.5% (2.94 kg of 4.11 kg total input) aligns with established powder management protocols. All recovered powder undergoes sieve analysis and chemical verification before reuse.

### 5.2 Waste Disposal

Non-recoverable materials were properly characterized and disposed of according to environmental regulations.

| Waste Stream | Quantity | Disposition Method | Documentation |
|--------------|----------|-------------------|---------------|
| Solid waste from water atomization | 0.41 kg | Landfill disposal | Waste manifest #WM-44892 |
| Non-recyclable 316L powder from SLM | 0.01 kg | Landfill disposal | Waste manifest #WM-44893 |

**Compliance Note:** All waste streams were characterized as non-hazardous per TCLP testing. Disposal was conducted through approved waste management vendors with complete chain of custody documentation.

---

## 6.0 Process Parameter Verification

### 6.1 SLM Process Parameters

Critical process parameters were monitored and recorded throughout the build cycle. All parameters remained within established control limits.

| Parameter | Setpoint | Actual Range | Control Limit | Status |
|-----------|----------|--------------|---------------|--------|
| Laser power | 275 W | 273-277 W | ±10 W | Within limits |
| Scan speed | 800 mm/s | 795-805 mm/s | ±15 mm/s | Within limits |
| Layer thickness | 30 μm | 30 μm | Fixed | Within limits |
| Build chamber oxygen | <0.1% | 0.03-0.07% | <0.1% | Within limits |
| Build plate temperature | 80°C | 79-81°C | ±3°C | Within limits |

### 6.2 Build Chamber Environment

The argon atmosphere was maintained throughout the process with the following characteristics:
- Initial chamber purge: 700 liters
- Continuous flow rate: Equivalent to 54 liters per component
- Oxygen content: Consistently below 0.1%
- Pressure: Maintained at 10-15 mbar above ambient

The total argon consumption of 3.08 kg reflects standard operation for a build of this duration and component count.

---

## 7.0 Non-Conformities and Corrective Actions

No major non-conformities were identified during this inspection. One minor observation was noted:

**Observation #1:** Powder handling documentation showed a 15-minute gap in humidity recording during transfer operations.

**Action Taken:** Procedure QP-PH-02 was reviewed with the responsible technician. Additional training on continuous monitoring requirements was completed. No product quality impact was identified.

---

## 8.0 Conclusions and Compliance Statement

Based on the comprehensive inspection conducted, the following conclusions are drawn:

1. All thirty-three (33) 316L stainless steel flat washers conform to specified dimensional, visual, and material requirements.

2. Manufacturing process parameters were maintained within established control limits throughout the production cycle.

3. Material consumption, energy usage, and by-product management were properly documented and aligned with standard operating procedures.

4. The process demonstrated effective material utilization with 71.5% powder reuse and minimal waste generation.

5. All quality records are complete and properly maintained.

**Compliance Statement:** This manufacturing lot meets all requirements specified in drawing #D-316L-WASHER-20x10.5x2.0 and associated quality plan QP-AM-316L-01. The components are approved for shipment to the customer.

---

**Approvals:**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Quality Engineer | J. Rodriguez | *Electronic Signature* | 10/26/2023 |
| Production Supervisor | M. Chen | *Electronic Signature* | 10/26/2023 |
| Quality Manager | R. Johnson | *Electronic Signature* | 10/27/2023 |

**Distribution:** Quality Department, Production Records, Customer File (as required)

---
*This report represents the findings at the time of inspection. Retain for a minimum of 10 years per quality records retention policy QP-RET-03.*