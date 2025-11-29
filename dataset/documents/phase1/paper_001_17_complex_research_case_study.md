# Case Study: Resource Efficiency and Process Analysis in Selective Laser Melting of 316L Stainless Steel Flat Washers

## Abstract

This comprehensive case study examines the manufacturing process for 316L stainless steel flat washers produced through selective laser melting (SLM) with water-atomized powder feedstock. The research documents detailed material flows, energy consumption parameters, and resource recovery rates across the integrated powder production and additive manufacturing workflow. Through systematic data collection during production cycles, we characterized the fundamental process parameters governing material utilization, energy demands, and waste generation. The study provides a granular view of operational metrics that influence manufacturing efficiency, with particular attention to the interplay between powder production via water atomization and subsequent laser melting operations. Findings reveal significant opportunities for material conservation through internal recycling loops while identifying key energy-intensive process stages. This work contributes to the growing body of knowledge on resource-efficient metal additive manufacturing practices.

## 1 Introduction

Selective laser melting has emerged as a prominent metal additive manufacturing technology, particularly for applications requiring complex geometries, customized designs, and rapid prototyping capabilities. The manufacturing of standard components such as flat washers through SLM represents an interesting case where traditional manufacturing approaches compete with emerging additive techniques. This study focuses specifically on 316L stainless steel, a corrosion-resistant austenitic stainless steel widely used in chemical processing, marine environments, and medical devices.

The integration of powder production via water atomization with subsequent SLM processing creates a manufacturing chain with distinct resource consumption characteristics. Understanding the material and energy flows through this integrated system is essential for optimizing process efficiency and environmental performance. While numerous studies have examined the mechanical properties and dimensional accuracy of SLM-produced components, fewer have provided detailed accounts of the resource metabolism at the process level.

This case study addresses this gap by documenting a complete production cycle for 316L stainless steel flat washers, tracking all significant material inputs, energy parameters, and output streams. The research aims to establish baseline data for future process improvements and technological comparisons. By maintaining focus on operational parameters rather than aggregated metrics, this work provides the foundational data necessary for engineers and researchers to model and optimize similar manufacturing systems.

## 2 Methodology

### 2.1 Process Overview

The manufacturing process documented in this study comprises two primary stages: powder production via water atomization and component fabrication through selective laser melting. The water atomization process converts bulk X2CrNiMo1712 stainless steel (the base composition for 316L) into fine powder suitable for SLM processing. This powder then serves as feedstock for the SLM system, where flat washers are built layer-by-layer using a laser energy source.

The SLM process occurred within an inert argon atmosphere to prevent oxidation during melting. Following each build cycle, unused powder was recovered for either immediate reuse in subsequent SLM operations or return to the water atomization process for remelting and reprocessing. The washers produced measured 20mm in outer diameter, 10mm in inner diameter, and 2mm in thickness, representing a standard flat washer configuration.

### 2.2 Data Collection Framework

Data collection focused on a single complete production cycle encompassing both powder production and SLM operations. All measurements were taken using calibrated instrumentation traceable to national standards. Mass measurements utilized precision scales with ±0.01g accuracy, while energy consumption data derived from power analyzers with ±1% measurement uncertainty. Gas flows were monitored using mass flow meters, and processing times were recorded through the machine control system.

The production cycle documented manufactured 33 flat washers in a single SLM build, representing a typical batch size for this component geometry. Powder for this batch was produced in a dedicated water atomization run, allowing for complete tracking of material from raw input to finished components and waste streams.

### 2.3 Key Process Parameters

The following parameters were established through preliminary characterization and remained constant throughout the documented production cycle:

**Water Atomization Parameters:**
- Energy consumption for melting: 2.23 MJ per kg of stainless steel processed
- Water-to-metal ratio maintained at approximately 4:1 by mass

**SLM Process Parameters:**
- Processing time per working cycle: 13.38 hours
- Nominal power consumption with laser active: 5.5 kW
- Nominal power consumption with laser inactive (system idle): 3.5 kW
- Argon gas volume required per component: 54 liters
- Argon gas volume for initial chamber filling: 700 liters
- Number of components per SLM working cycle: 33 pieces
- Layer thickness: 30μm
- Laser scan speed: 800 mm/s
- Build platform temperature: 80°C

## 3 Results

### 3.1 Material Inputs

The material inputs for the documented production cycle are summarized in Table 1. Both direct material consumption and the parameters governing calculable flows are presented to provide complete transparency regarding resource utilization.

**Table 1: Material Inputs for SLM Washer Production**

| Material Input | Type | Value | Unit | Notes |
|----------------|------|-------|------|--------|
| X2CrNiMo1712 stainless steel for powder atomization | Direct | 4.11 | kg | Base material for water atomization |
| Process water for water atomization | Direct | 16.8 | kg | Cooling and atomization media |
| Argon shielding and processing gas | Calculable | - | - | Based on volume parameters below |
| → SLM argon volume per component | Parameter | 54 | L | Consumption rate during processing |
| → SLM argon volume for chamber filling | Parameter | 700 | L | Initial atmosphere establishment |
| → Number of components per SLM working cycle | Parameter | 33 | pieces | Batch size for gas calculation |

The argon consumption represents a significant process input, with utilization driven by both per-component processing needs and initial chamber preparation. The relationship between component count and total gas requirement follows a linear model once the fixed chamber volume is accounted for.

### 3.2 Energy Consumption

Energy consumption occurred primarily in two process stages: powder production via water atomization and component fabrication through SLM. The parameters governing energy use in each stage are documented in Table 2.

**Table 2: Energy Consumption Parameters**

| Energy Flow | Type | Parameters | Value | Unit |
|-------------|------|------------|-------|------|
| LV electricity for water atomization | Calculable | WA energy consumption for melting | 2.23 | MJ/kg |
| | | X2CrNiMo1712 stainless steel for powder atomization | 4.11 | kg |
| LV electricity for Selective Laser Melting | Calculable | SLM processing time per working cycle | 13.38 | h |
| | | SLM nominal power with laser on | 5.5 | kW |
| | | SLM nominal power with laser off | 3.5 | kW |

The SLM process exhibited variable power demand throughout the build cycle, with higher consumption during active laser melting and lower consumption during recoating and positioning operations. The ratio of laser-active to laser-inactive time was approximately 65:35 based on machine monitoring data.

Historical data from previous production runs (last year: ~70-75 kWh for similar component batches) suggests incremental improvements in energy efficiency, likely attributable to optimized laser parameters and reduced support structures.

### 3.3 Outputs and Resource Recovery

The manufacturing process generated multiple output streams, including finished products, recovered materials for reuse, and waste requiring disposal. These outputs are detailed in Table 3.

**Table 3: Process Outputs and Recovery Streams**

| Output | Type | Value | Unit | Notes |
|--------|------|-------|------|--------|
| Flat washers (316L, finished parts) | Direct | 0.61 | kg | Total mass of 33 washers |
| Flat washers (316L, finished parts) | Direct | 33 | units | Total quantity produced |
| 316L powder reused within SLM process | Direct | 2.94 | kg | Immediately recyclable powder |
| 316L powder returned to WA for remelting | Direct | 0.15 | kg | Powder requiring reprocessing |
| Recovered process water from water atomization | Direct | 16.4 | kg | Water recycled within system |
| Solid waste from water atomization sent to landfill | Direct | 0.41 | kg | Oxidized material and impurities |
| Non-recyclable 316L powder from SLM sent to landfill | Direct | 0.01 | kg | Contaminated or sintered powder |

The material efficiency of the process can be assessed through the recovery rates. Approximately 71.5% of input powder was converted directly to reusable powder or finished components, while 3.6% required remelting, and 0.2% was lost as non-recyclable waste. The water recovery rate of 97.6% demonstrates effective closed-loop operation in the atomization system.

Industry benchmarks for similar processes typically show powder reuse rates of 65-85% for well-optimized SLM systems, placing this implementation in the mid-to-upper range of performance.

## 4 Discussion

### 4.1 Material Flow Analysis

The documented material flows reveal a manufacturing system with sophisticated internal recycling mechanisms. The high rate of powder reuse within the SLM process (2.94 kg from a total powder input of approximately 4.11 kg) demonstrates the operational advantage of powder-bed additive manufacturing technologies. However, the accumulation of minor losses through multiple cycles—particularly the 0.41 kg solid waste from water atomization and 0.01 kg non-recyclable powder from SLM—suggests potential areas for process refinement.

The relationship between initial material input and final product output shows that approximately 14.8% of the raw stainless steel was converted into finished washers, with the majority of material maintained within the recycling loops. This low direct conversion efficiency is characteristic of powder-bed processes but is offset by the high recyclability of unused powder.

The water atomization process generated measurable solid waste (0.41 kg), primarily consisting of oxidized material and impurities separated during atomization. This represents an inherent limitation of water atomization compared to gas atomization, though the latter typically carries higher energy and gas consumption penalties.

### 4.2 Energy Consumption Patterns

The energy parameters documented reveal distinct consumption profiles for the two main process stages. The water atomization energy intensity of 2.23 MJ/kg aligns with typical values for industrial water atomization systems, which generally range from 2.0-2.5 MJ/kg for stainless steels.

The SLM process energy parameters show significant base load consumption even when the laser is inactive (3.5 kW), highlighting the importance of build chamber heating, atmosphere control, and system electronics. The differential between laser-active and laser-inactive power consumption (2.0 kW) represents the direct energy input for melting. The extended processing time of 13.38 hours for 33 washers reflects the relatively small component size and the layer-by-layer nature of the process.

Comparative analysis with conventional manufacturing approaches for similar components would need to account for the different allocation of energy across manufacturing stages. Traditional machining of washers from sheet or bar stock eliminates powder production energy but introduces significant material removal losses.

### 4.3 Process Integration and Optimization Opportunities

The integration of water atomization with SLM creates a manufacturing system with complementary strengths and limitations. The water atomization process provides cost-effective powder production but generates aqueous waste streams and has lower powder sphericity compared to gas atomization. The SLM process effectively utilizes the powder but requires protective atmosphere and has limited build rates.

The argon consumption parameters indicate that gas usage is dominated by the fixed chamber volume requirement rather than per-component processing needs. This suggests potential efficiency gains through equipment redesign to minimize chamber volume or through process modifications that enable higher component density per build.

The energy parameters for SLM operation show that reducing processing time would have a compound effect on energy efficiency, simultaneously decreasing both the base load and active melting consumption. Strategies for time reduction include optimized scan patterns, higher laser power, or improved heating and cooling cycles.

## 5 Conclusions

This case study has provided a detailed documentation of resource flows in an integrated SLM manufacturing process for 316L stainless steel flat washers. The key findings include:

1. The manufacturing system demonstrates effective material conservation through internal recycling, with over 95% of input powder remaining in productive use through either immediate reuse or reprocessing.

2. Energy consumption is distributed across powder production and component fabrication stages, with significant base load requirements in the SLM process that are independent of laser operation.

3. Argon consumption follows a mixed model with both fixed and variable components, suggesting different optimization approaches for each consumption driver.

4. Waste generation is minimal but occurs at multiple points in the process, primarily during powder production and from contaminated powder in the SLM process.

The parameters documented in this study provide a foundation for future process optimization and technology comparison. Specific recommendations for improvement include exploration of alternative powder production methods with lower waste generation, implementation of energy-saving modes during SLM system idle periods, and redesign of the SLM build chamber to reduce inert gas requirements.

Future work should focus on dynamic modeling of the documented parameters to predict resource consumption under varying production scenarios and component geometries. Additionally, longitudinal studies tracking material degradation through multiple recycling cycles would provide valuable insights into long-term process sustainability.

## 6 Acknowledgments

The authors thank the technical staff at the Advanced Manufacturing Research Centre for their assistance in data collection and process documentation. This research was supported through internal funding allocated to manufacturing process characterization initiatives.

---

*Document ID: CS-SLM-316L-Washer-2023*
*Confidentiality: Internal Research Document*
*Revision: 1.0*