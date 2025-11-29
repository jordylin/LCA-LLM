# Build Job Log: Selective Laser Melting of 316L Stainless Steel Flat Washers

## Job Information

**Job ID:** WAS-316L-240520-01  
**Date:** May 20, 2024  
**Operator:** M. Chen (Shift B)  
**Machine:** SLM Solutions 280 HL  
**Build Platform:** Standard 280mm × 280mm  
**Part Description:** ASTM A276 316L stainless steel flat washers  
**Target Quantity:** 33 pieces  
**Scheduled Duration:** 14 hours (including setup and cooldown)

**Pre-Build Checklist Completed:** 07:45  
- Safety systems verified  
- Argon supply pressure: 185 bar (within operating range)  
- Process water circulation: Normal  
- Powder sieving system: Clean and operational  
- Build platform: Leveled and cleaned  
- Laser calibration: Within specification

## Build Preparation and Material Loading

**Timestamp:** 08:00  
**Activity:** Powder loading and system initialization

Fresh X2CrNiMo1712 stainless steel powder for atomization: 4.11 kg loaded into feedstock hopper.

Process water for water atomization system: 16.8 kg measured and added to cooling circuit.

**Timestamp:** 08:20  
**Activity:** Chamber purging sequence initiated

Argon chamber filling volume: 700 L standard procedure  
Argon consumption rate during build: 54 L per component

Build file loaded: "Washer_316L_33pc.sli"  
Layer thickness: 30 μm  
Laser scan strategy: Stripes with 67° rotation

## Build Process Execution

**Timestamp:** 08:45  
**Activity:** Build sequence started  
Chamber oxygen level: 78 ppm (within specification <100 ppm)  
Build platform preheat temperature: 80°C

**Process Parameters:**
- Processing time per working cycle: 13.38 hours
- Laser nominal power when active: 5.5 kW
- Machine nominal power when laser off: 3.5 kW
- Number of components per SLM working cycle: 33 pieces

**Timestamp:** 09:15  
**Activity:** First layers completed  
Laser power stability: Within ±2%  
Powder recoating: Normal operation  
Chamber temperature: 32°C

**Timestamp:** 12:30  
**Activity:** Mid-build inspection  
Layer 450 of 1,120 completed  
Powder bed quality: Uniform, no irregularities  
Laser focus: Maintained within tolerance

**Timestamp:** 16:00  
**Activity:** Process monitoring  
Chamber oxygen level: 82 ppm  
Cooling water temperature: 24°C  
Powder feed rate: Consistent

**Timestamp:** 20:15  
**Activity:** System status check  
Argon supply pressure: 162 bar  
Process water level: Normal  
Vibration sensors: All within green range

**Timestamp:** 22:05  
**Activity:** Build completion  
Final layer deposited  
Total active processing time: 13.38 hours  
Laser operating hours logged: Machine total now 1,847.3 hours

## Material Consumption and Usage Data

**Raw Materials Input:**

| Material Type | Quantity | Purpose |
|---------------|----------|---------|
| X2CrNiMo1712 stainless steel powder | 4.11 kg | Feedstock for water atomization |
| Process water | 16.8 kg | Cooling media for atomization |

**Gas Consumption Parameters:**
- Argon volume per component: 54 L
- Number of components in build: 33 pieces
- Chamber filling volume: 700 L
- Total argon volume calculated from above parameters

**Energy Usage Parameters:**

Water atomization process:
- Energy consumption rate for melting: 2.23 MJ per kg of material processed
- Material processed: 4.11 kg

SLM process energy parameters:
- Processing duration: 13.38 hours
- Machine power with laser active: 5.5 kW
- Machine power with laser inactive: 3.5 kW

*Reference: Previous similar job (April 15, 2024) used 13.5 hours processing time with comparable power settings.*

## Product Output and Quality

**Timestamp:** 22:30  
**Activity:** Build platform removal and initial inspection

**Finished Parts Data:**

| Parameter | Value |
|-----------|-------|
| Total parts produced | 33 units |
| Total mass of finished washers | 0.61 kg |
| Visual inspection pass rate | 100% |
| Dimensional verification | Within drawing tolerance |

**First Article Measurement:**
- Outer diameter: 19.05 mm ±0.05 mm
- Inner diameter: 9.53 mm ±0.05 mm
- Thickness: 1.52 mm ±0.03 mm
- Surface roughness: Ra 12-15 μm (as-built condition)

## Material Recovery and Waste Management

**Timestamp:** 23:00  
**Activity:** Powder recovery and sieving

**Recovered Materials:**

| Material Type | Quantity | Disposition |
|---------------|----------|-------------|
| 316L powder reused in SLM process | 2.94 kg | Returned to process hopper |
| 316L powder returned for remelting | 0.15 kg | Sent to water atomization |
| Recovered process water | 16.4 kg | Returned to cooling system |

**Waste Streams:**

| Waste Type | Quantity | Disposition |
|------------|----------|-------------|
| Solid waste from water atomization | 0.41 kg | Landfill disposal |
| Non-recyclable 316L powder | 0.01 kg | Landfill disposal |

**Powder Recycling Efficiency:** 94.2% of unused powder recovered for reuse

*Note: Industry benchmark for powder reuse typically 90-95% for 316L applications.*

## Equipment Performance and Maintenance Notes

**Machine Performance Summary:**
- Laser uptime: 100% (no interruptions)
- Powder delivery system: No blockages
- Recuperation system: Normal operation
- Cooling system: Stable temperature control

**Maintenance Performed:**
- Filter replacement: Not required this cycle
- Lens cleaning: Scheduled after next build
- Rail lubrication: Completed during setup

**Alarms and Events:**
- 14:22: Minor fluctuation in powder feed sensor (auto-corrected)
- 19:45: Temporary chamber temperature rise to 35°C (returned to normal within 2 minutes)

## Post-Build Procedures

**Timestamp:** 23:45  
**Activity:** System shutdown and cleanup

Build platform moved to depowdering station  
Chamber cleaned and prepared for next job  
Argon supply valve closed  
Process water system drained and flushed

**Next Maintenance Due:** 
- Laser source: 2,000 hours (152.7 hours remaining)
- Filter replacement: Next build
- Full calibration: 2,500 hours

## Operator Comments and Sign-off

**Operator Notes:** 
"Build completed without significant issues. Powder consumption slightly lower than estimated. All parts visually acceptable. Recommend continuing current parameter set for future washer production."

**Quality Control:** 
Parts sent to post-processing for stress relief and inspection.

**Build Status:** COMPLETED SUCCESSFULLY

**Signed:** 
M. Chen, Operator  
Date: May 21, 2024 00:15

**Verified:** 
A. Rodriguez, Process Engineer  
Date: May 21, 2024 08:30

---
*End of Build Job Log WAS-316L-240520-01*