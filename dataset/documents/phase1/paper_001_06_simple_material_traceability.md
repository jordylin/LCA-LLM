# Material Traceability Report: Selective Laser Melting of 316L Stainless Steel Flat Washers

**Document ID:** MTR-SLM-316L-2023-047  
**Revision:** 1.0  
**Date:** October 26, 2023  
**Prepared by:** Quality Assurance Department, Advanced Manufacturing Division  
**Approved by:** Dr. Elena Rodriguez, Head of Quality Assurance  

---

## Executive Summary

This report documents the complete material traceability for production lot SLM-BUILD-033, comprising 33 units of 316L stainless steel flat washers manufactured via Selective Laser Melting (SLM). The traceability chain covers material receipt through powder production, additive manufacturing, and final disposition, with verification of mass balance across all process stages. All material movements are documented with corresponding weighing records and lot identifiers to ensure compliance with ISO 9001:2015 and internal quality management system requirements. The production cycle demonstrated effective material utilization with 92.3% of input powder recovered for reuse or recycling.

## 1.0 Introduction and Scope

### 1.1 Purpose
This material traceability report provides a comprehensive accounting of all material flows associated with the manufacturing of 316L stainless steel flat washers using Selective Laser Melting technology. The documentation serves to verify material integrity throughout the production process and support quality assurance protocols.

### 1.2 Process Overview
The manufacturing process involves two primary stages: water atomization of stainless steel to produce powder feedstock, followed by SLM processing to fabricate the final components. Material tracking begins with raw material receipt and continues through all transformation stages to final product shipment and waste disposition.

### 1.3 Document Scope
This report covers production cycle SLM-BUILD-033 completed on October 15, 2023, including all associated material receipts, transformations, and dispositions. Traceability is maintained through unique identifier assignment at each process stage.

## 2.0 Material Receiving and Initial Verification

### 2.1 Raw Material Receipt
The base material for powder production was received on October 10, 2023, with the following specifications:

| Material Parameter | Specification |
|-------------------|---------------|
| Material Grade | X2CrNiMo1712 (316L equivalent) |
| Supplier | Global Steel Alloys, Lot #GSA-316L-2309 |
| Certificate of Analysis | COA-8675301 |
| Received Quantity | 4.11 kg |
| Receiving Inspector | J. Wilkins |

The material underwent incoming inspection including visual examination, verification of material certification, and weight confirmation using calibrated Mettler Toledo XS204 scale (Calibration Cert. CAL-445-2023).

### 2.2 Material Verification Protocol
All raw materials are verified against purchase order specifications prior to release to production. The 4.11 kg of X2CrNiMo1712 stainless steel was confirmed to meet chemical composition requirements per mill certificate and was assigned internal tracking number RM-316L-2301.

## 3.0 Powder Production via Water Atomization

### 3.1 Process Description
Water atomization transforms the solid stainless steel feedstock into fine powder suitable for SLM processing. The process involves melting the raw material and dispersing it with high-pressure water jets to form spherical powder particles.

### 3.2 Material Inputs and Outputs
The water atomization process for this production lot consumed the following inputs and generated the documented outputs:

| Material Flow | Quantity | Unit | Tracking Reference |
|---------------|----------|------|-------------------|
| **Inputs** | | | |
| X2CrNiMo1712 stainless steel | 4.11 | kg | RM-316L-2301 |
| Process water | 16.8 | kg | WTR-ATOM-103 |
| Electricity consumption | 2.55 | kWh | MET-EL-4452 |
| **Outputs** | | | |
| 316L powder for SLM | 3.09 | kg | POW-316L-2310A |
| Recovered process water | 16.4 | kg | WTR-REC-208 |
| Solid waste to landfill | 0.41 | kg | WASTE-SOL-119 |

*Historical context: Previous production runs typically yielded 3.05-3.12 kg of powder from 4.11 kg input, with water recovery rates consistently around 97-98%.*

### 3.3 Process Parameters
The water atomization was conducted using Atomization System AT-7 with the following operational parameters:

- Melting energy consumption: 2.23 MJ per kg of material processed
- Water pressure: 120 bar
- Atomization temperature: 1580°C
- Powder particle size distribution: 15-45 μm (verified per ISO 13320)

The 0.41 kg of solid waste consisted primarily of oversize particles and slag, which was containerized in drum WASTE-119 for disposal at approved landfill facility.

## 4.0 Selective Laser Melting Process

### 4.1 Build Preparation
The SLM process utilized an EOS M290 system (Serial #EOS-7824) with the following build parameters:

| Build Parameter | Specification |
|-----------------|---------------|
| Build ID | SLM-BUILD-033 |
| Machine | EOS M290 #7824 |
| Build Volume | 250 × 250 × 325 mm |
| Layer Thickness | 30 μm |
| Laser Power | 200 W |
| Scan Speed | 800 mm/s |
| Processing Time | 13.38 hours |
| Operator | M. Chen |

### 4.2 Material Consumption and Energy Usage
The SLM process consumed the following resources for build SLM-BUILD-033:

| Resource | Quantity | Unit | Calculation Basis |
|----------|----------|------|-------------------|
| 316L powder from atomization | 3.09 | kg | POW-316L-2310A |
| Argon shielding gas | 3.08 | kg | Calculated from gas volumes |
| Electricity consumption | 64.92 | kWh | Meter reading EL-MTR-889 |
| Processing time | 13.38 | hours | Machine log data |

The argon consumption of 3.08 kg was calculated based on the system's gas usage protocol, which includes 700 L for initial chamber purging plus 54 L per component for process gas during manufacturing.

The electricity consumption reflects the machine's operational profile with laser active at 5.5 kW and standby periods at 3.5 kW throughout the 13.38-hour build cycle.

### 4.3 Process Monitoring and Control
The build process was monitored continuously with real-time parameter logging. All process parameters remained within established control limits throughout the build duration. Oxygen levels in the process chamber were maintained below 100 ppm, confirming proper inert atmosphere integrity.

## 5.0 Product Output and Quality Verification

### 5.1 Finished Component Specifications
The SLM process produced 33 flat washers with the following characteristics:

| Product Attribute | Specification |
|-------------------|---------------|
| Component | Flat Washer (316L) |
| Quantity | 33 units |
| Total Mass | 0.61 kg |
| Part Number | FW-316L-10MM |
| Average Unit Mass | 18.48 g |
| Build ID | SLM-BUILD-033 |

### 5.2 Quality Inspection Results
All 33 components underwent dimensional verification and visual inspection per drawing FW-316L-10MM-REV-C. Inspection records confirmed all parts met specified tolerances (±0.1 mm on critical dimensions). Two random samples underwent metallurgical analysis, confirming proper fusion and absence of significant defects.

## 6.0 Material Recovery and Waste Management

### 6.1 Powder Recovery and Reuse
Following the SLM build process, unused powder was systematically recovered and categorized:

| Powder Category | Quantity | Unit | Disposition |
|-----------------|----------|------|-------------|
| Powder reused in SLM | 2.94 | kg | Returned to powder handling system |
| Powder returned for remelting | 0.15 | kg | Shipped to water atomization facility |
| Non-recyclable powder to landfill | 0.01 | kg | Container WASTE-PWD-045 |

The powder recovery efficiency of 95.1% exceeds the departmental target of 90% for 316L stainless steel processes. The 0.01 kg of non-recyclable powder consisted of contaminated material from the build plate edges.

### 6.2 Water Recovery in Atomization
The water atomization process demonstrated effective water conservation with 16.4 kg of process water recovered from the 16.8 kg input, representing a 97.6% recovery rate. The recovered water was filtered and returned to the atomization system reservoir for reuse in subsequent production cycles.

### 6.3 Waste Stream Management
All waste materials were properly containerized, labeled, and tracked for disposition:

| Waste Stream | Quantity | Unit | Disposition |
|--------------|----------|------|-------------|
| Solid waste from atomization | 0.41 | kg | Landfill (WASTE-SOL-119) |
| Non-recyclable powder | 0.01 | kg | Landfill (WASTE-PWD-045) |
| Total Waste | 0.42 | kg | - |

*Industry benchmark: Typical waste generation for similar SLM processes ranges from 0.35-0.50 kg per production cycle of this scale.*

## 7.0 Mass Balance Analysis

### 7.1 Comprehensive Material Accounting
The complete mass balance for production lot SLM-BUILD-033 is summarized below:

| Material Category | Input (kg) | Output (kg) | Balance |
|-------------------|------------|-------------|---------|
| **Raw Materials** | | | |
| X2CrNiMo1712 stainless steel | 4.11 | - | - |
| Process water | 16.8 | - | - |
| **Products** | | | |
| Finished washers | - | 0.61 | - |
| **Recovered Materials** | | | |
| Powder reused in SLM | - | 2.94 | - |
| Powder returned for remelting | - | 0.15 | - |
| Recovered process water | - | 16.4 | - |
| **Waste** | | | |
| Solid waste to landfill | - | 0.41 | - |
| Non-recyclable powder | - | 0.01 | - |
| **Total** | 20.91 | 20.52 | -0.39 |

The mass balance shows a minor discrepancy of 0.39 kg (1.9% of total mass), which falls within acceptable limits for measurement uncertainty and process losses. This variance is attributed primarily to material adhesion to equipment surfaces and evaporation during processing.

### 7.2 Material Utilization Efficiency
The overall material utilization for this production cycle was calculated as follows:

- Powder conversion to product: 19.7% (0.61 kg product / 3.09 kg powder)
- Total material recovery rate: 92.3% (19.50 kg recovered / 21.12 kg total input)
- Net new material consumption: 8.5% (1.80 kg net consumption / 21.12 kg total input)

*Historical comparison: The powder conversion rate of 19.7% represents a 2.1% improvement over the facility average of 19.3% for similar components.*

## 8.0 Chain of Custody Documentation

### 8.1 Material Tracking System
All material movements were documented through the facility's electronic tracking system (MAT-TRAC v4.2) with the following key transactions:

| Transaction | Date | Material | From | To | Quantity | Verified By |
|-------------|------|----------|------|----|----------|-------------|
| RM Receipt | 10/10/23 | X2CrNiMo1712 | Supplier | Raw Stock | 4.11 kg | J. Wilkins |
| Powder Production | 10/12/23 | 316L Powder | Raw Stock | Powder Inventory | 3.09 kg | T. Gupta |
| SLM Build | 10/15/23 | 316L Powder | Powder Inventory | SLM Machine | 3.09 kg | M. Chen |
| Product Output | 10/16/23 | Finished Washers | SLM Machine | QC | 0.61 kg | A. Kowalski |
| Powder Recovery | 10/16/23 | Reusable Powder | SLM Machine | Powder Inventory | 2.94 kg | M. Chen |

### 8.2 Documentation Compliance
All material movements are supported by corresponding documentation including weigh tickets, material transfer forms, and electronic system entries. The complete documentation package has been archived per records retention policy QMS-REC-005 (7-year retention period).

## 9.0 Conclusions and Recommendations

### 9.1 Traceability Verification
The material traceability for production lot SLM-BUILD-033 has been fully verified with complete documentation of all material flows from receipt through final disposition. All material movements are properly documented and the mass balance demonstrates acceptable accounting accuracy.

### 9.2 Process Performance
The SLM process demonstrated efficient material utilization with strong recovery rates for both metal powder and process water. The 92.3% total material recovery rate exceeds the departmental target of 90% for 316L stainless steel components.

### 9.3 Recommendations
Based on the analysis of this production cycle, the following recommendations are proposed:

1. Continue the current powder handling protocols which have demonstrated excellent recovery efficiency
2. Investigate opportunities to reduce the minor mass balance variance through improved cleaning procedures
3. Maintain the water recovery system performance through scheduled maintenance per manufacturer specifications

### 9.4 Compliance Statement
This production lot and associated material flows comply with all applicable quality system requirements and regulatory standards. All waste dispositions were conducted in accordance with environmental permit conditions and facility procedures.

---

**Document History:**  
Revision 1.0: Initial release  
**Distribution:** Quality Assurance, Production Management, Environmental Compliance, Records Archive