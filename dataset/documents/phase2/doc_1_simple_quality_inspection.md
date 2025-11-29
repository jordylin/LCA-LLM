# Quality Inspection Report for Selective Laser Melting of Ti6Al4V Femoral Stems

**Report ID:** QIR-SLM-2023-087  
**Date of Inspection:** October 15, 2023  
**Inspector:** Dr. Elena Rodriguez, Senior Quality Engineer  
**Batch Reference:** FS-Ti64-Batch-20-0923  
**Machine:** EOS M 290 Metal Additive Manufacturing System  
**Build Job ID:** BJ-2023-0412  

---

## Executive Summary

This report documents the quality inspection for the selective laser melting (SLM) production of twenty (20) medical-grade Ti6Al4V femoral stems. The build process was completed successfully, with all components conforming to specified dimensional, material, and procedural requirements. The inspection verifies that the manufacturing process adhered to established protocols, with precise tracking of material inputs, energy consumption, and output flows. All twenty stems passed the rigorous inspection criteria, confirming their suitability for subsequent finishing and sterilization processes prior to clinical use.

---

## 1. Introduction

The femoral stems produced in this batch are intended for use in orthopedic hip arthroplasty, requiring exceptional mechanical integrity, biocompatibility, and dimensional accuracy. The SLM process employed utilizes a high-power laser to selectively melt titanium alloy powder in an inert argon atmosphere, building components layer-by-layer. This inspection ensures that the manufacturing process complies with internal quality management systems and relevant industry standards, including ASTM F2924 for Ti6Al4V components and ISO 13485 for medical device quality systems.

The build was conducted as a single job containing twenty identical femoral stem components, optimized for nesting within the build chamber to maximize efficiency. Support structures were incorporated to manage thermal stresses and facilitate post-processing removal.

---

## 2. Inspection Scope and Objectives

**Scope:** This inspection covers the complete SLM build process for Batch FS-Ti64-Batch-20-0923, including pre-build preparation, in-process monitoring, and post-build verification.

**Objectives:**
- Verify conformance of final components to design specifications.
- Document all material and energy inputs utilized during the build.
- Quantify and categorize all output materials, including products, recyclable powder, and waste streams.
- Ensure process parameters remained within validated operating windows.
- Provide traceable records for regulatory and customer audit purposes.

**Inspection Criteria:**
- Dimensional accuracy within ±0.1 mm of CAD model specifications.
- Visual inspection for surface defects, cracks, or irregularities.
- Material usage and waste tracking against expected yields.
- Energy consumption verification against machine performance data.
- Compliance with argon purity and consumption standards.

---

## 3. Inspection Procedures and Methods

### 3.1 Pre-Build Verification
Prior to initiation, the SLM machine underwent calibration and maintenance checks. The build chamber was verified for leak integrity, and argon purity was confirmed to exceed 99.995%. The Ti6Al4V powder lot was certified to ASTM F2924 Grade 23 standards, with particle size distribution between 15-45 μm.

### 3.2 In-Process Monitoring
Throughout the 61.35-hour build duration, machine parameters were continuously logged. Key monitored parameters included:
- Laser power: Maintained at 400 W.
- Scan speed and hatch spacing: As per optimized parameters for Ti6Al4V.
- Chamber oxygen levels: Consistently below 100 ppm.
- Bed temperature: Controlled at 80°C.

### 3.3 Post-Build Inspection
Upon completion, the build plate was removed and components were separated from support structures using wire EDM. The following inspections were performed:
- **Visual Inspection:** All components examined under 10x magnification for surface defects.
- **Dimensional Verification:** Critical dimensions measured using coordinate measuring machine (CMM) with 5 μm accuracy.
- **Weight Measurement:** Individual components and material flows weighed using calibrated scales with 0.001 g resolution.
- **Powder Handling:** Unmelted powder sieved and tested for reuse eligibility per internal protocols.

---

## 4. Build Process and Resource Documentation

### 4.1 Build Parameters Summary

| Parameter | Value | Notes |
|-----------|-------|-------|
| Number of Components | 20 stems | Single build job |
| Total Build Time | 61.35 hours | From start to chamber cool-down |
| Average Machine Power | 2.4 kW | Measured at machine input |
| Laser Power | 400 W | Constant throughout build |
| Layer Thickness | 30 μm | Standard for Ti6Al4V |
| Build Platform Temperature | 80°C | Maintained within ±5°C |

### 4.2 Material and Energy Inputs

All material and energy inputs were measured and recorded during the build process. The quantities represent actual consumption for the complete build job.

| Input Category | Material/Energy Type | Quantity | Unit |
|----------------|----------------------|----------|------|
| Raw Material | Ti6Al4V Powder (Grade 23) | 20.83 | kg |
| Process Gas | Argon (Chamber Flooding) | 3.03 | kg |
| Process Gas | Argon (Building Phase) | 25.94 | kg |
| Process Energy | Electricity (SLM Process) | 147.26 | kWh |

**Contextual Note:** The total argon consumption of 28.97 kg represents standard usage for maintaining inert atmosphere throughout the build cycle. Chamber flooding occurs during initial purge, while building phase consumption maintains atmosphere during laser operation.

### 4.3 Output Materials and Waste Streams

The outputs from the build process were carefully segregated and quantified. All material flows are reported as total masses for the complete build.

| Output Category | Material Type | Quantity | Unit | Disposition |
|-----------------|---------------|----------|------|-------------|
| Product | Ti6Al4V Femoral Stems (with supports) | 1.77 | kg | To finishing department |
| Recovered Material | Unmelted Loose Powder | 18.99 | kg | To powder recycling |
| Waste | Support Structures & Minor Losses | 0.019 | kg | To metal recycling |
| Waste | Filter-Captured Metal Powder | 0.0208 | kg | To approved landfill |

**Powder Recovery Note:** The unmelted powder underwent sieving and contamination testing, confirming eligibility for reuse in future medical device builds. The high recovery rate of approximately 91.2% is consistent with optimized powder management practices.

**Historical Comparison:** In previous builds of similar geometry (2022 average), powder usage efficiency averaged 89.5%, indicating continued process optimization.

---

## 5. Dimensional Verification Results

All twenty femoral stems underwent comprehensive dimensional inspection using Brown & Sharpe Global Advantage CMM with PC-DMIS measurement software. The inspection followed the first article inspection plan, measuring 32 critical features per component against the master CAD model.

### 5.1 Key Dimensional Measurements

| Feature | Specification (mm) | Average Measured (mm) | Tolerance | Conformance |
|---------|---------------------|------------------------|-----------|-------------|
| Stem Length | 145.00 ±0.10 | 145.02 | ±0.08 | Pass |
| Neck Diameter | 12.50 ±0.05 | 12.49 | ±0.04 | Pass |
| Platform Width | 42.00 ±0.15 | 41.98 | ±0.12 | Pass |
| Taper Angle | 5°40' ±0°05' | 5°39' | ±0°03' | Pass |

All measured dimensions fell within the specified tolerances, with no outliers detected. The maximum deviation recorded was 0.07 mm on the medial curvature, well within the allowable ±0.10 mm tolerance.

### 5.2 Surface Quality Assessment

Surface roughness measurements were taken using Mitutoyo Surftest SJ-410 profilometer. The as-built surfaces showed Ra values between 10-15 μm, consistent with expectations for SLM Ti6Al4V components. No visible defects, cracks, or inclusions were observed during microscopic examination.

---

## 6. Material and Process Conformance

### 6.1 Material Traceability

The Ti6Al4V powder lot (Lot #P-Ti64-2309-18) was fully traceable to mill certificates confirming chemical composition within ASTM F2924 requirements:
- Aluminum: 5.5-6.5% (measured: 6.2%)
- Vanadium: 3.5-4.5% (measured: 4.1%)
- Oxygen: <0.13% (measured: 0.08%)
- Iron: <0.25% (measured: 0.16%)

### 6.2 Process Parameter Verification

All critical process parameters remained within validated ranges throughout the build:
- Laser power stability: ±2% of setpoint
- Scan speed consistency: ±1.5% variation
- Chamber temperature: 80°C ±3°C
- Oxygen levels: consistently 40-60 ppm

### 6.3 Energy Consumption Analysis

The total electricity consumption of 147.26 kWh aligns with expectations for a 61.35-hour build at an average power draw of 2.4 kW. This includes laser operation, chamber heating, cooling systems, and ancillary equipment.

**Industry Reference:** Typical energy consumption for similar SLM builds ranges from 140-160 kWh for comparable component mass and build time.

---

## 7. Waste Management and Environmental Compliance

The waste streams generated during this build were minimal and properly managed according to established protocols:

- **Recyclable Materials (18.99 kg):** Unmelted powder undergoes sieving, testing, and blending with virgin powder for reuse in non-critical applications.
- **Metal Recycling (0.019 kg):** Support structures and machining swarf are collected and sent to certified metal recyclers.
- **Landfill Waste (0.0208 kg):** Filter-captured powder, contaminated during filtration, is disposed of in accordance with hazardous waste regulations.

All waste handling procedures comply with internal environmental management systems and regulatory requirements for titanium processing.

---

## 8. Conclusions and Recommendations

### 8.1 Inspection Findings

- All twenty Ti6Al4V femoral stems meet or exceed all specified quality requirements.
- Dimensional accuracy is within acceptable tolerances for medical implant applications.
- Material usage efficiency demonstrates effective process optimization.
- Energy consumption aligns with expected values for the build duration and complexity.
- Waste generation is minimal and properly managed through approved channels.

### 8.2 Conformance Statement

Based on the comprehensive inspection detailed in this report, Batch FS-Ti64-Batch-20-0923 is confirmed to conform to all applicable quality standards and specifications. The components are approved for release to the finishing department for support structure removal, surface treatment, and final inspection.

### 8.3 Recommendations for Continuous Improvement

1. **Process Optimization:** Consider evaluating alternative support structure designs to further reduce material waste in future builds.
2. **Powder Management:** Continue monitoring powder reuse cycles to maintain material properties within specification.
3. **Energy Efficiency:** Investigate potential for reduced argon consumption through optimized gas flow controls.

---

**Approval Signatures:**

**Inspector:** ___________________________  
Dr. Elena Rodriguez, Senior Quality Engineer  
Date: ___________________________  

**Quality Manager:** ___________________________  
Mr. James Chen, Quality Assurance Manager  
Date: ___________________________  

**Document Control:** This report has been archived under reference QIR-SLM-2023-087 and is valid for three years from the date of issue.

---  
*End of Report*