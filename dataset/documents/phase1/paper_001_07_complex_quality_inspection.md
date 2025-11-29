# Quality Inspection Report for Selective Laser Melting (SLM) of 316L Stainless Steel Flat Washers

**Report Number:** QIR-SLM-316L-2023-047
**Date of Inspection:** October 26, 2023
**Inspection Lead:** Maria Rodriguez, Senior Quality Engineer
**Customer Reference:** PO-8842-B, Flat Washers Lot #FW-316L-33B
**Applicable Standards:** ASTM F3184-16 (Standard Specification for Additive Manufacturing Stainless Steel Alloy), ISO/ASTM 52902 (Additive manufacturing — Test artifacts), Internal Quality Procedure QP-AM-07

---

## 1.0 Executive Summary

This report documents the quality inspection for production lot #FW-316L-33B comprising thirty-three (33) 316L stainless steel flat washers manufactured via Selective Laser Melting (SLM). The inspection was conducted to verify conformance to dimensional, material, and process specifications. All inspected washers met the acceptance criteria outlined in section 4.0. The manufacturing batch is approved for shipment and certified to meet the specified requirements.

**Overall Finding:** **PASS** - All acceptance criteria satisfied.

---

## 2.0 Introduction and Scope

This inspection covers the complete manufacturing cycle for 316L stainless steel flat washers produced on the SLM 280HL system (Serial #HL-280-88921). The scope includes verification of:
- Raw material composition and handling
- Powder production via water atomization
- SLM process parameters and gas management
- Final part dimensions, mass, and visual quality
- Waste and material recovery streams

The inspection was performed as part of routine quality assurance and in response to customer PO-8842-B.

---

## 3.0 Materials and Consumables Verification

### 3.1 Raw Material Inputs

All raw materials were verified against material certificates and internal receiving reports.

| Material Description | Certificate Number | Quantity Verified | Unit | Status |
|---------------------|-------------------|-------------------|------|--------|
| X2CrNiMo1712 stainless steel for powder atomization (316L base material) | C-7717-AM | 4.11 | kg | Conforms |
| Process water for water atomization of 316L powder | N/A (Plant supply) | 16.8 | kg | Conforms |

**Notes:** Base material chemistry was verified via spectrometer analysis against ASTM A276. Water quality met plant standards for conductivity (<50 µS/cm).

### 3.2 Process Gases and Utilities

Process gas consumption is governed by established machine parameters. For this production cycle:

- **Argon Shielding Gas:** The SLM process utilized argon with the following operational parameters:
  - Chamber pre-purge and fill volume: 700 liters
  - Continuous flow rate during processing: Equivalent to 54 liters per component
  - Total components in build chamber: 33 pieces

**Verification:** Argon supply pressure and flow rates were monitored throughout the 13.38-hour build cycle and remained within specified tolerances.

### 3.3 Energy Consumption Parameters

Energy usage is monitored per established machine and process parameters:

- **Water Atomization Process:** Energy consumption for powder production is characterized by a specific energy input of 2.23 MJ per kilogram of stainless steel processed.
- **SLM Process Energy:** The SLM 280HL system operated for a total processing time of 13.38 hours. Machine power consumption is defined by two primary states:
  - Nominal power with laser active: 5.5 kW
  - Nominal power with laser inactive (idle/pre-heat): 3.5 kW

Power monitoring logs confirmed stable operation within these parameters throughout the build cycle.

---

## 4.0 Inspection Procedures and Acceptance Criteria

### 4.1 Dimensional Inspection

All 33 washers were measured using a Mitutoyo CMM (Model CRYSTA-Apex S 121210) with 1 µm accuracy. Critical dimensions were verified against drawing #DW-316L-WSH-02.

| Dimension | Specification | Tolerance | Measurement Method |
|-----------|---------------|-----------|-------------------|
| Outer Diameter | 20.0 mm | ±0.1 mm | CMM - 4-point average |
| Inner Diameter | 10.5 mm | ±0.05 mm | CMM - 4-point average |
| Thickness | 2.0 mm | ±0.05 mm | Digital micrometer |
| Flatness | - | 0.1 mm max | Surface plate and indicator |

### 4.2 Visual and Surface Inspection

Visual inspection was performed per ASTM F3122-14 using 10x magnification under controlled lighting.

**Acceptance Criteria:**
- No visible cracks or delamination
- Surface roughness (Ra) ≤ 12 µm per customer specification
- Minimal partially fused powder particles (< 3 per cm²)
- No significant discoloration or oxidation

### 4.3 Mass Verification

Each washer was weighed on a Mettler Toledo XS204 analytical balance (0.1 mg resolution). Target mass per washer: 18.48 g ± 0.5 g.

---

## 5.0 Inspection Results

### 5.1 Dimensional Results Summary

All 33 components met dimensional specifications. Representative data from first, middle, and last components in build plate:

| Sample Position | Outer Diameter (mm) | Inner Diameter (mm) | Thickness (mm) | Flatness (mm) |
|-----------------|---------------------|---------------------|----------------|---------------|
| 1 (Front-Left) | 20.02 | 10.48 | 2.01 | 0.08 |
| 17 (Center) | 19.99 | 10.52 | 1.99 | 0.06 |
| 33 (Rear-Right) | 20.01 | 10.51 | 2.02 | 0.07 |
| **Average** | **20.01** | **10.50** | **2.01** | **0.07** |

**Finding:** All dimensional measurements within specified tolerances.

### 5.2 Mass Verification Results

Total mass of finished washers: 0.61 kg (33 pieces)

| Statistical Parameter | Value |
|----------------------|-------|
| Average Mass per Washer | 18.48 g |
| Standard Deviation | 0.12 g |
| Range (Min-Max) | 18.32 g - 18.63 g |
| Within Tolerance? | Yes |

**Finding:** Mass distribution consistent and within specification.

### 5.3 Surface Quality and Visual Inspection

Surface roughness measurements averaged Ra = 9.8 µm (range: 8.5-11.2 µm). No components exhibited cracking, delamination, or significant discoloration. Partially fused powder particles averaged 1.2 per cm², well below the rejection limit.

**Finding:** Surface quality acceptable.

### 5.4 Material Balance and Recovery

Post-process material accounting verified the following streams:

| Material Stream | Quantity | Unit | Disposition |
|----------------|----------|------|-------------|
| Finished Flat Washers (316L) | 0.61 | kg | Approved for shipment |
| 316L Powder Reused in SLM Process | 2.94 | kg | Returned to powder handling system |
| 316L Powder Returned for Remelting | 0.15 | kg | Sent to water atomization facility |
| Recovered Process Water from Atomization | 16.4 | kg | Returned to water treatment system |
| Solid Waste from Water Atomization | 0.41 | kg | Sent to approved landfill |
| Non-recyclable 316L Powder from SLM | 0.01 | kg | Sent to approved landfill |

**Verification:** Material reconciliation shows 99.2% accountability against inputs.

---

## 6.0 Non-Conformances and Observations

No major non-conformances were identified during this inspection.

**Minor Observation:** Slight variation in surface texture was noted between components from center versus edge positions on the build plate. This is consistent with expected process variation and remains within acceptable limits for this application.

---

## 7.0 Conclusions and Certification

Based on the comprehensive inspection detailed in this report:

- All 316L stainless steel flat washers in lot #FW-316L-33B conform to specified requirements
- Manufacturing processes were conducted within established parameters
- Material handling and recovery procedures were properly executed
- No quality issues requiring corrective action were identified

**Certification Statement:** The undersigned certifies that the products covered by this inspection report were manufactured and inspected in accordance with the specified requirements and are approved for release to the customer.

---
**Inspector Signature:** _________________________

**Maria Rodriguez**
Senior Quality Engineer
Additive Manufacturing Division

**Date:** October 26, 2023

---

*Document Reference: This report supersedes any preliminary inspection data. Maintained in quality records for minimum 10 years per QMS procedure QP-DOC-03.*