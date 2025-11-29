# Process Development Report: Selective Laser Melting of ER70 Steel Marine Propeller with 1 mm Machining Allowance

## Executive Summary

This document details the comprehensive development process for manufacturing marine propellers from ER70 steel using Selective Laser Melting (SLM) technology. The project successfully transitioned from conceptual design to a production-ready process capable of delivering high-quality propellers with consistent mechanical properties. Key achievements include the optimization of gas atomization parameters for powder production, refinement of SLM build parameters to minimize defects, and development of efficient post-processing techniques. The finalized process consumes 0.352 kg of ER70 steel powder and 11.49 kWh of electricity during the SLM build phase to produce a 0.204 kg propeller, with an additional 2.84 kWh for finish machining. This report documents the technical journey, parameter evolution, challenges overcome, and lessons learned throughout the development cycle.

---

## 1. Introduction

### 1.1 Project Background
The marine industry's increasing demand for complex, customized propeller designs with reduced lead times motivated the exploration of additive manufacturing technologies. Traditional casting and machining methods often involve extended production cycles and significant material waste. Selective Laser Melting (SLM) was identified as a promising alternative due to its ability to produce near-net-shape components with intricate geometries. This project focused on developing a reliable SLM process for ER70 steel marine propellers, incorporating a 1 mm machining allowance to ensure dimensional accuracy and surface finish.

### 1.2 Development Objectives
- Establish a repeatable powder production process using gas atomization
- Optimize SLM parameters to achieve >99.5% density in as-built parts
- Develop efficient support structures to minimize post-processing effort
- Integrate finish machining to meet final dimensional tolerances
- Characterize process inputs and outputs for production planning

---

## 2. Process Overview

The manufacturing process comprises three primary stages: feedstock preparation via gas atomization, SLM build process, and post-processing through finish machining. Each stage underwent extensive development to optimize efficiency and quality.

**Development Timeline:**
- Phase 1 (Months 1-3): Feedstock characterization and atomization parameter studies
- Phase 2 (Months 4-8): SLM parameter optimization and support structure design
- Phase 3 (Months 9-12): Integration of post-processing and final validation

---

## 3. Feedstock Development: Gas Atomization Process

### 3.1 Initial Challenges and Parameter Studies
Early development focused on producing consistent ER70 steel powder with optimal morphology for SLM processing. Initial atomization trials resulted in irregular particle shapes and satellite formation, leading to poor flowability and inconsistent layer deposition during SLM.

Parameter optimization addressed several key factors:
- Melt superheat temperature: Optimized to 1550°C to ensure proper fluidity
- Atomization gas pressure: Finalized at 3.2 MPa for consistent particle size distribution
- Nozzle design: Modified to reduce satellite formation and improve yield

Comparative data from development phases showed significant improvement:
- Initial trials: Powder yield ~65% with 30% satellites
- Optimized process: Powder yield >85% with <5% satellites

### 3.2 Feedstock Process Parameters and Consumption

The finalized gas atomization process demonstrated consistent performance with the following consumption data for producing ER70 steel powder:

| Material/Energy Input | Quantity | Unit |
|-----------------------|----------|------|
| Steel billet for powder production | 0.414 | kg |
| Electricity for gas atomization | 0.828 | kWh |
| Argon for gas atomization | 2.58 | kg |
| Water for cooling | 0.116 | kg |

**Output:**
- ER70 steel powder (including supports): 0.352 kg

The electricity intensity of the gas atomization process was measured at 2 kWh per kg of powder produced, aligning with industry benchmarks for similar alloy systems. During development, we reduced argon consumption by 15% compared to initial parameter sets through improved nozzle design and gas flow optimization.

---

## 4. SLM Build Process Development

### 4.1 Parameter Optimization Journey
The SLM parameter development followed a systematic approach, beginning with single-track experiments and progressing to multi-layer cubes before final propeller geometries. Key parameters requiring optimization included laser power, scan speed, hatch spacing, and layer thickness.

**Major Development Milestones:**
- **Laser Power**: Initial range 150-350W, finalized at 280W for optimal melt pool stability
- **Scan Speed**: Optimized to 800 mm/s to balance productivity and defect formation
- **Layer Thickness**: Selected 30μm based on powder characteristics and resolution requirements
- **Support Structure**: Developed custom conical supports reducing material usage by 22% compared to standard lattice designs

### 4.2 Build Chamber Atmosphere and Process Gases
Maintaining proper atmosphere proved critical for preventing oxidation and ensuring consistent mechanical properties. After testing various gas flow rates and distribution systems, we established optimal parameters using argon as the primary atmosphere gas with compressed air for ancillary functions.

### 4.3 SLM Process Consumption Data

The finalized SLM build process for a single marine propeller demonstrated the following consumption patterns:

| Input | Quantity | Unit |
|-------|----------|------|
| ER70 steel powder (including supports) | 0.352 | kg |
| Electricity for SLM build | 11.49 | kWh |
| Compressed air | 3.56 | m³ |
| Argon for build chamber | 1.2 | m³ |

**Process Context:**
- Total build time: 6.55 hours
- Average power consumption during build: 1.75 kW

Early development builds showed approximately 20% higher electricity consumption due to suboptimal scan strategies and unnecessary laser idling. Through parameter refinement and improved build file preparation, we achieved the current efficiency levels.

---

## 5. Post-processing: Finish Machining Development

### 5.1 Machining Strategy Evolution
The 1 mm machining allowance required careful planning to balance material removal efficiency with surface finish requirements. Initial machining trials encountered challenges with tool wear and surface defects due to the unique microstructure of SLM-produced ER70 steel.

**Key Developments:**
- **Tool Selection**: Transitioned from standard carbide to specialized coated tools, increasing tool life by 35%
- **Cutting Parameters**: Optimized speeds and feeds to account for material heterogeneity
- **Fixture Design**: Developed custom fixtures minimizing deflection and vibration

### 5.2 Coolant and Fluid Management
Cutting fluid selection and application methodology underwent significant refinement. Early approaches used flood cooling, but we transitioned to minimum quantity lubrication (MQL) for improved efficiency and reduced fluid consumption.

### 5.3 Finish Machining Consumption Data

The optimized finish machining process for the marine propeller required:

| Input | Quantity | Unit |
|-------|----------|------|
| Electricity for finish machining | 2.84 | kWh |
| Cutting fluid | 1.94 | kg |

**Process Context:**
- Finish machining time: 4.133 hours
- Average power consumption: 0.687 kW

Compared to initial machining trials, we reduced cutting fluid consumption by approximately 28% through the implementation of MQL and improved chip management.

---

## 6. Integrated Process Performance

### 6.1 Overall Material Flow and Efficiency
The complete manufacturing process demonstrates efficient material utilization from raw billet to finished product. The material flow can be summarized as:

| Component | Quantity | Unit |
|-----------|----------|------|
| **Inputs** | | |
| Steel billet for powder production | 0.414 | kg |
| ER70 steel powder (including supports) | 0.352 | kg |
| **Outputs** | | |
| Marine propeller (ER70 steel) | 0.204 | kg, 1 unit |
| Machined chips from 1 mm allowance | 0.116 | kg |

The overall material efficiency from billet to finished propeller is approximately 49.3%, with the balance accounted for by powder production losses (14.9%) and machining chips (28.0%).

### 6.2 Energy Consumption Profile
Total electrical energy consumption across all process stages amounts to 15.158 kWh per propeller, distributed as follows:
- Gas atomization: 0.828 kWh (5.5%)
- SLM build: 11.49 kWh (75.8%)
- Finish machining: 2.84 kWh (18.7%)

During development, we reduced total energy consumption by approximately 18% compared to initial process configurations through equipment optimization and parameter refinement.

### 6.3 Process Challenges and Solutions

**Major Technical Challenges Encountered:**

1. **Powder Reuse Degradation**
   - *Problem*: Mechanical properties deteriorated after multiple powder reuse cycles
   - *Solution*: Implemented strict powder handling procedures and limited reuse to 5 cycles maximum

2. **Support Structure Removal**
   - *Problem*: Difficult removal causing surface damage
   - *Solution*: Developed breakaway support design with controlled fracture points

3. **Residual Stress Management**
   - *Problem*: Distortion during machining due to residual stresses
   - *Solution*: Incorporated stress relief heat treatment before machining

4. **Build Failures from Contamination**
   - *Problem*: Intermittent build failures traced to powder contamination
   - *Solution*: Enhanced powder sieving and storage protocols

---

## 7. Conclusions and Recommendations

### 7.1 Key Development Outcomes
The SLM process for ER70 steel marine propellers has been successfully developed and validated for production implementation. The process demonstrates consistent performance with well-characterized input requirements and output yields. The integration of gas atomization, SLM building, and finish machining creates a viable manufacturing route for complex marine components.

### 7.2 Lessons Learned
- Powder quality consistency is paramount for reliable SLM processing
- Support structure design requires balancing build reliability with post-processing effort
- SLM material microstructure necessitates specialized machining approaches
- Comprehensive process documentation enables trouble-free production transfer

### 7.3 Recommendations for Future Development
1. Explore alternative support structure materials to reduce post-processing
2. Investigate in-situ monitoring for real-time process control
3. Develop recycling protocols for machining chips
4. Optimize build orientation for reduced machining requirements

### 7.4 Production Readiness Assessment
The process has met all development objectives and is ready for production implementation. The characterized input requirements enable accurate production planning and cost estimation. Ongoing monitoring during initial production runs will focus on process stability and continuous improvement opportunities.

---

## Appendices

### Appendix A: Complete Process Consumption Summary

| Process Stage | Material/Energy Input | Quantity | Unit |
|---------------|----------------------|----------|------|
| Gas Atomization | Steel billet | 0.414 | kg |
| | Electricity | 0.828 | kWh |
| | Argon | 2.58 | kg |
| | Water | 0.116 | kg |
| SLM Build | ER70 steel powder | 0.352 | kg |
| | Electricity | 11.49 | kWh |
| | Compressed air | 3.56 | m³ |
| | Argon | 1.2 | m³ |
| Finish Machining | Electricity | 2.84 | kWh |
| | Cutting fluid | 1.94 | kg |

**Output Summary:**
- Marine propeller (ER70 steel): 0.204 kg, 1 unit
- Machined chips: 0.116 kg

### Appendix B: Process Parameter History
*Note: The following data represents historical development iterations and is provided for context only. Current production parameters are documented in the main report.*

| Development Phase | SLM Electricity (kWh) | Machining Electricity (kWh) | Notes |
|------------------|------------------------|-----------------------------|-------|
| Initial Trials | ~14.2 | ~3.5 | High porosity, frequent build failures |
| Intermediate | ~12.8 | ~3.1 | Improved scan strategy, reduced defects |
| Final Optimized | 11.49 | 2.84 | Current production parameters |

---

*Report Prepared by: Process Engineering Department*
*Date: [Current Date]*
*Document Version: 1.0*