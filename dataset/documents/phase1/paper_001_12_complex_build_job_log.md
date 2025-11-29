# Build Job Log: Selective Laser Melting (SLM) of 316L Stainless Steel Flat Washers

## Job Information

**Job ID:** SLM-JOB-2023-001  
**Date:** 2023-10-05  
**Operator:** John Doe  
**Machine:** SLM Solutions 280HL  
**Part Description:** 316L Stainless Steel Flat Washers  
**Build Platform:** Standard 280 x 280 mm  
**Job Status:** Completed Successfully  

**Overview:** This log documents the complete build cycle for 33 units of 316L stainless steel flat washers using selective laser melting technology. The job involved powder preparation via water atomization and subsequent additive manufacturing process.

## Material Inputs and Preparation

### Raw Materials Consumption

| Material Type | Quantity | Batch Number | Notes |
|---------------|----------|--------------|-------|
| X2CrNiMo1712 Stainless Steel for Powder Production | 4.11 kg | STL-316L-2309 | Virgin material for water atomization |
| Process Water for Atomization | 16.8 kg | H2O-2309-C | Demineralized water, cooling circuit |

**Powder Preparation Notes:** The stainless steel feedstock was processed through the water atomization unit to produce fine powder suitable for SLM processing. Water served as both cooling and fragmentation media during atomization.

## Process Parameters and Settings

### Water Atomization System Configuration

- Melting energy specification: 2.23 MJ per kg of material processed
- Total material processed through atomizer: 4.11 kg
- Water pressure maintained: 150-200 bar
- Nozzle configuration: Standard 316L settings

### SLM Machine Configuration

| Parameter | Value | Unit | Notes |
|-----------|-------|------|-------|
| Build Chamber Dimensions | 280 × 280 × 365 | mm | Standard platform |
| Layer Thickness | 30 | μm | Standard for 316L |
| Laser Power (Active) | 200 | W | Continuous wave |
| Scan Speed | 800 | mm/s | Optimized for washers |
| Hatch Distance | 120 | μm | Standard spacing |
| Build Platform Temperature | 80 | °C | Pre-heat setting |

**SLM Operational Parameters:**
- Total processing duration for complete job: 13.38 hours
- Machine power consumption during laser operation: 5.5 kW
- Machine power consumption during non-laser phases: 3.5 kW
- Number of components in single build cycle: 33 pieces

## Gas System Operation

### Argon Atmosphere Management

**Initial Chamber Preparation:**
- Chamber purging volume: 700 liters
- Oxygen level after purging: < 100 ppm
- Purge duration: 45 minutes

**Continuous Gas Usage During Build:**
- Argon consumption rate: 54 liters per component
- Total components processed: 33 pieces
- Gas flow maintained throughout build: 15 L/min
- Pressure regulation: 12-15 mbar above atmospheric

## Energy Consumption Parameters

### Water Atomization Energy Input

- Specific energy requirement for melting: 2.23 MJ per kilogram of material
- Total material mass processed: 4.11 kg
- Atomization system efficiency: Standard operating range

### SLM Process Energy Profile

- Build duration: 13.38 hours continuous operation
- Active laser power draw: 5.5 kW
- Standby/system power: 3.5 kW
- Laser duty cycle: Approximately 65% active time

*Historical Comparison: Previous similar job (SLM-JOB-2023-000) showed processing time of 14.2 hours with comparable power settings.*

## Operational Event Log

**Timestamp:** 2023-10-05 07:30  
**Event:** Machine startup and pre-heat sequence initiated  
**Status:** Normal  
**Operator:** John Doe  
**Notes:** Build platform heating to 80°C, system checks passed

**Timestamp:** 2023-10-05 08:15  
**Event:** Chamber argon purging commenced  
**Status:** Normal  
**Oxygen Level:** 850 ppm (initial)  
**Notes:** Standard purging procedure initiated

**Timestamp:** 2023-10-05 09:00  
**Event:** Chamber atmosphere established  
**Status:** Normal  
**Oxygen Level:** 85 ppm  
**Notes:** Build process ready to initiate

**Timestamp:** 2023-10-05 09:15  
**Event:** Layer deposition and laser melting initiated  
**Status:** Normal  
**Layer Count:** 1 of 2033  
**Notes:** First layer completed successfully, recoater operation normal

**Timestamp:** 2023-10-05 22:33  
**Event:** Build process completion  
**Status:** Normal  
**Layer Count:** 2033 completed  
**Notes:** All layers processed, system entering cool-down phase

## Output Quantification

### Manufactured Components

| Component Type | Quantity | Total Mass | Quality Status |
|----------------|----------|------------|----------------|
| 316L Stainless Steel Flat Washers | 33 units | 0.61 kg | Passed visual inspection |

### Material Recovery and Reuse

| Material Stream | Quantity | Destination/Use |
|-----------------|----------|-----------------|
| 316L Powder Recovered for SLM Reuse | 2.94 kg | Returned to SLM powder handling system |
| 316L Powder for Water Atomization Remelting | 0.15 kg | Transferred to powder production area |
| Recovered Process Water from Atomization | 16.4 kg | Returned to water treatment system |

## Waste Streams

| Waste Category | Quantity | Disposition Method |
|----------------|----------|---------------------|
| Solid Residue from Water Atomization | 0.41 kg | Landfill disposal per standard procedure |
| Non-recyclable 316L Powder from SLM | 0.01 kg | Landfill disposal, contaminated material |

## System Performance and Maintenance

### Equipment Status During Build

**SLM Machine Performance:**
- Laser uptime: 99.8%
- Recoater operation: Normal, zero failures
- Powder delivery: Consistent flow
- Temperature stability: ±2°C throughout build

**Cooling System:**
- Chiller operation: Normal
- Temperature control: Within specified range
- No alarms or interventions required

### Maintenance Activities

**Pre-Build Maintenance:**
- Optics cleaning: Completed
- Recoater blade inspection: Within tolerance
- Powder sieve check: Passed

**Post-Build Maintenance:**
- Build chamber cleaning: Scheduled
- Filter replacement: Not required
- System calibration: Verified within specifications

## Quality Control Notes

**In-Process Monitoring:**
- Layer consistency: Uniform throughout build
- Melt pool monitoring: Stable
- No delamination observed
- Powder bed quality: Consistent

**Post-Build Inspection:**
- All 33 washers visually acceptable
- No visible defects or distortions
- Dimensions within specified tolerances
- Ready for post-processing if required

## Operational Summary

The build job completed successfully within the planned timeframe. All system parameters remained within operational specifications throughout the 13.38-hour processing period. The material consumption and output quantities align with expected values for this component geometry and quantity.

**Key Performance Indicators:**
- Build success rate: 100% (33/33 components)
- Powder utilization efficiency: Standard range
- Gas consumption: As per established parameters
- Energy profile: Consistent with machine specifications

**Follow-up Actions:**
- Post-process inspection scheduled
- Powder recycling procedure initiated
- System ready for next job after standard maintenance

---

*Document generated: 2023-10-06  
Approved by: John Doe, Senior Operator  
Next scheduled maintenance: 2023-10-20*