# Build Job Log: Selective Laser Melting of Ti6Al4V Femoral Stems - Batch 20

**Job ID:** SLM-FS-2023-045  
**Machine:** SLM Solutions 280HL (Serial: HL-2874)  
**Operator:** J. Rodriguez (Shift B)  
**Build Start:** 2023-10-15 08:00  
**Build End:** 2023-10-17 21:21  
**Total Duration:** 61.35 hours  

---

## 1.0 Job Overview

This document records the operational data for build job SLM-FS-2023-045, involving the additive manufacturing of twenty (20) medical-grade Ti6Al4V femoral stems using Selective Laser Melting technology. The build was executed on the SLM280HL system in Bay 3 of the Advanced Manufacturing Center. All procedures followed standard operating protocols for medical device production, with continuous monitoring by the automated system and periodic checks by the operator.

The primary objective was to produce a full batch of 20 stems with consistent metallurgical properties and dimensional accuracy. The build plate was configured for optimal packing density, and all pre-build calibrations were completed per the equipment maintenance schedule.

---

## 2.0 Build Parameters

Key operational settings and contextual parameters for this build job are summarized below. These parameters were maintained within specified tolerances throughout the process, with no significant deviations recorded.

| Parameter | Value | Unit | Notes |
|-----------|-------|------|-------|
| Laser Power | 400 | W | Constant throughout build |
| Scan Speed | 1200 | mm/s | Standard for Ti6Al4V |
| Layer Thickness | 30 | μm | As per build file |
| Build Chamber Temperature | 150 | °C | Pre-heated and maintained |
| Total Build Time | 61.35 | hours | From start to cool-down completion |
| Number of Parts | 20 | stems | Femoral stem design Rev. 2.1 |
| Average Machine Power Draw | 2.4 | kW | Measured at main supply |

*Historical Note: Previous similar build (SLM-FS-2023-032) averaged 2.3 kW power consumption over 59.8 hours.*

---

## 3.0 Material and Gas Consumption

### 3.1 Raw Material Inventory

Ti6Al4V powder, gas atomized (GA) grade, was used for this build. The powder was sourced from certified supplier AP&C, lot #TGA-2309, with particle size distribution of 15-45 μm. Powder handling followed nitrogen-purged procedures to minimize oxidation risk.

| Material Type | Quantity | Unit | Status |
|---------------|----------|------|---------|
| Ti6Al4V Powder (GA) | 20.83 | kg | Loaded at start |

### 3.2 Process Gas Usage

High-purity argon (99.999%) was utilized for both chamber flooding and continuous building phase protection. Gas consumption was automatically logged by the mass flow controllers.

| Gas Application | Quantity | Unit | Purpose |
|-----------------|----------|------|---------|
| Chamber Flooding | 3.03 | kg | Initial atmosphere establishment |
| Building Phase | 25.94 | kg | Continuous oxygen suppression |

*Reference: Industry typical argon consumption for similar Ti builds ranges 25-30 kg.*

---

## 4.0 Energy Consumption

Electrical power consumption was monitored via the machine's integrated power meter and cross-verified with facility smart meters. The recorded values represent the total energy used during the complete build cycle, including pre-heat, build, and controlled cool-down phases.

| Energy Type | Consumption | Unit | Application |
|-------------|-------------|------|-------------|
| Electricity | 147.26 | kWh | SLM build process |

The average power draw of 2.4 kW aligns with expected performance for this machine configuration under continuous operation. Minor fluctuations occurred during recoater blade cycles and laser calibration sequences, but remained within acceptable bounds.

---

## 5.0 Operational Timeline

### 5.1 Pre-Build Phase (2023-10-15 07:30-08:00)

- **07:30** - Operator verification completed; build plate installed and leveled
- **07:45** - Powder loading initiated; 20.83 kg Ti6Al4V powder dispensed into feed modules
- **07:55** - Chamber sealing confirmed; leak test passed at 5.2 mbar/min
- **07:58** - Argon flooding commenced; oxygen levels dropped below 100 ppm within 12 minutes

### 5.2 Build Execution Phase (2023-10-15 08:00 - 2023-10-17 18:00)

- **08:00** - Build initiation; laser calibration completed successfully
- **08:15** - First layer melted; process parameters stable
- **Hour 4.5** - Recoater blade maintenance cycle completed; no powder spreading issues
- **Hour 28.3** - Mid-build inspection via chamber camera; no visible anomalies
- **Hour 52.7** - Automatic powder replenishment from secondary feed module
- **Hour 61.0** - Final layer completed; laser system deactivated

### 5.3 Post-Process Phase (2023-10-17 18:00-21:21)

- **18:15** - Controlled cool-down initiated; temperature ramp rate 5°C/min
- **19:30** - Chamber venting with nitrogen; oxygen levels monitored
- **20:45** - Build chamber access; visual inspection satisfactory
- **21:00** - Powder recovery system activated
- **21:21** - Build plate removal and transfer to depowdering station

Throughout the build, system sensors recorded temperature stability within ±3°C of setpoint and oxygen levels consistently below 50 ppm. No process interruptions or alarms were triggered.

---

## 6.0 Output and Waste Management

### 6.1 Product Output

Twenty Ti6Al4V femoral stems were successfully manufactured, including integrated support structures designed for optimal thermal management during building.

| Output Type | Quantity | Mass | Unit | Notes |
|-------------|----------|------|------|-------|
| Ti6Al4V Femoral Stems | 20 | 1.77 | kg | Includes support structures |

### 6.2 Material Recovery

Unmelted powder was recovered using the integrated sieving and recycling system. The recovered powder will be characterized and blended with virgin material for future builds per the material recycling protocol.

| Material Type | Quantity | Unit | Disposition |
|---------------|----------|------|-------------|
| Unmelted Loose Powder | 18.99 | kg | Recyclable - sent to characterization |

### 6.3 Waste Streams

Two primary waste streams were generated during post-processing. All waste handling complied with facility environmental management procedures.

| Waste Type | Quantity | Unit | Disposition |
|------------|----------|------|-------------|
| Support Structures & Minor Losses | 0.019 | kg | Sent to metal recycling |
| Filter-Captured Metal Powder | 0.0208 | kg | To approved landfill |

The minimal waste generation (total 0.0398 kg) demonstrates efficient material utilization, with approximately 95.2% of input powder either converted to product or recovered for reuse.

---

## 7.0 Equipment Performance Notes

The SLM280HL system operated within all specified parameters throughout the 61.35-hour build. Key performance indicators:

- Laser uptime: 99.8% (scheduled calibration cycles only)
- Recoater system: Zero failures or interventions required
- Vacuum system: Stable with no leak detection events
- Cooling system: Maintained setpoint ±0.5°C
- Filter pressure drop: Remained below 60% of maximum

Preventive maintenance is scheduled per the 200-hour cycle, with next service due after approximately three more similar builds.

---

## 8.0 Quality Control Checkpoints

- **Pre-build**: Powder quality certification verified (Certificate of Analysis #COA-TGA-2309)
- **Layer 50**: In-process monitoring showed consistent melt pool characteristics
- **Post-build**: Visual inspection confirmed all parts present with no obvious defects
- **Dimensional**: Initial measurements of two sample stems within ±0.1mm of CAD model

Parts have been transferred to the post-processing department for support removal, heat treatment, and final inspection. Build data has been archived per quality management system requirements.

---

## 9.0 Summary

Build job SLM-FS-2023-045 was completed successfully within the scheduled timeframe. All operational parameters remained stable, and the material consumption aligns with expectations for this part geometry and build configuration. The high powder recovery rate (18.99 kg of 20.83 kg input) indicates effective process control and minimal spillage or contamination.

**Key Performance Metrics:**
- Build success rate: 100% (20/20 parts)
- Material utilization efficiency: 8.5% to part, 91.1% recovered
- Energy intensity: 7.36 kWh per stem
- Build rate: 0.33 stems per hour

This log serves as the primary record for equipment performance tracking and will be referenced during periodic maintenance reviews and process optimization initiatives.

*Log certified complete by: J. Rodriguez, Senior AM Technician*
*Date: 2023-10-18*