# Build Job Log: Selective Laser Melting of ER70 Steel Marine Propeller

**Job ID:** SLM-2023-087  
**Product:** Marine Propeller (ER70 Steel)  
**Build Date:** October 15, 2023  
**Operator:** J. Doe  
**Machine:** SLM 280 HL  
**Post-Processing Equipment:** CNC Mill VM-2  

---

## Job Overview

This log documents the complete manufacturing process for a single ER70 steel marine propeller produced via Selective Laser Melting (SLM) with a 1 mm machining allowance. The process involved three primary phases: powder feedstock production via gas atomization, the SLM build itself, and final finish machining. All operational parameters, material consumptions, and energy usages are recorded as per standard procedure.

Key specifications:
- Target component weight: 0.204 kg
- Build platform: 280 x 280 mm
- Layer thickness: 30 µm
- Laser power: 400 W
- Scan speed: 800 mm/s
- Support structures: Custom lattice design

---

## Powder Production Phase – Gas Atomization

**Date:** October 10, 2023  
**Equipment:** Argon Gas Atomizer Unit GA-200  
**Operator:** A. Smith  

The ER70 steel powder was produced in-house using gas atomization. The process commenced at 08:00 and concluded at 12:30. Material and utility consumptions were monitored via integrated sensors.

**Process Parameters:**
- Melt temperature: 1650°C
- Argon pressure: 4.5 bar
- Water cooling flow rate: 12 L/min
- Atomization duration: 4.5 hours

**Material and Energy Consumption:**

| Item | Quantity | Unit | Notes |
|------|----------|------|-------|
| Steel billet input | 0.414 | kg | ER70 grade, certified |
| Electricity consumption | 0.828 | kWh | Mainly for induction melting and gas compression |
| Argon gas usage | 2.58 | kg | High-purity, 99.998% |
| Cooling water | 0.116 | kg | Closed-loop system, make-up water only |
| Powder output | 0.352 | kg | Sieved to 15-45 µm, yield ~85% |

**Sensor Readings (Averaged):**
- Melt chamber temperature: 1645-1655°C
- Argon flow rate: 55 L/min
- Power draw: 0.184 kW (average over 4.5 h)
- Cooling water temperature out: 35°C

No alarms or deviations recorded. Powder quality met specification with spherical morphology >95%.

---

## SLM Build Phase

**Date:** October 15, 2023  
**Equipment:** SLM 280 HL  
**Operator:** J. Doe  
**Build Start:** 06:00  
**Build End:** 12:33  
**Total Build Time:** 6.55 hours  

The build process was executed with standard parameters for ER70 steel. The job file "Propeller_B1.slm" was loaded, and the build chamber was purged and prepared.

**Build Parameters:**
- Layer count: 1100
- Recoater speed: 150 mm/s
- Chamber oxygen level: <0.1%
- Build plate temperature: 200°C

**Operational Log:**

| Time | Event / Parameter | Value | Unit | Notes |
|------|------------------|-------|------|-------|
| 06:00 | Build start | - | - | Chamber sealed, purge initiated |
| 06:15 | Oxygen level | 0.08 | % | Within spec |
| 06:20 | Powder deposition | - | - | First layer completed |
| 06:30 | Laser activation | - | - | Melting commenced |
| 06:30-12:30 | Average power draw | 1.75 | kW | Consistent throughout build |
| 12:33 | Build complete | - | - | Laser off, cool-down initiated |

**Material and Utility Consumption:**

| Item | Quantity | Unit | Notes |
|------|----------|------|-------|
| ER70 steel powder | 0.352 | kg | Including support structures |
| Electricity consumption | 11.49 | kWh | Total for build cycle |
| Compressed air | 3.56 | m³ | For powder handling and cleaning |
| Argon gas | 1.2 | m³ | For atmosphere control |

**Sensor Data (Averaged):**
- Laser power: 400 W
- Chamber temperature: 195-205°C
- Argon flow: 3.0 L/min
- Compressed air pressure: 6 bar

No system alarms. Build completed successfully with 100% density confirmed via in-process monitoring.

---

## Finish Machining Phase

**Date:** October 16, 2023  
**Equipment:** CNC Mill VM-2  
**Operator:** R. Brown  
**Start Time:** 08:00  
**End Time:** 12:08  
**Total Machining Time:** 4.133 hours  

The propeller was removed from the build plate and transferred to the CNC mill for finish machining to achieve final dimensions and surface finish. A 1 mm machining allowance was removed from all functional surfaces.

**Machining Parameters:**
- Spindle speed: 2500 RPM
- Feed rate: 200 mm/min
- Depth of cut: 0.5 mm (two passes)
- Tool: Carbide end mill, 10 mm diameter

**Operational Log:**

| Time | Event / Parameter | Value | Unit | Notes |
|------|------------------|-------|------|-------|
| 08:00 | Part setup | - | - | Fixturing completed |
| 08:15 | Coolant system on | - | - | Cutting fluid circulated |
| 08:20 | Machining start | - | - | First tool path |
| 08:20-12:08 | Average power draw | 0.687 | kW | Steady operation |
| 12:08 | Machining complete | - | - | Part unloaded |

**Material and Energy Consumption:**

| Item | Quantity | Unit | Notes |
|------|----------|------|-------|
| Electricity consumption | 2.84 | kWh | For spindle, axes, and auxiliaries |
| Cutting fluid | 1.94 | kg | Water-soluble oil, 5% concentration |
| Finished propeller | 0.204 | kg | 1 unit, meets drawing specs |
| Machined chips (waste) | 0.116 | kg | ER70 steel, collected for recycling |

**Sensor Readings:**
- Spindle load: 65-75%
- Coolant temperature: 22°C
- Tool wear: Within limits, no tool change required

No operational issues. Surface finish measured at Ra 1.6 µm, within tolerance.

---

## Summary of Material and Energy Flows

**Consolidated Data for Current Build:**

| Phase | Material / Utility | Quantity | Unit |
|-------|-------------------|----------|------|
| Powder Production | Steel billet | 0.414 | kg |
| Powder Production | Electricity | 0.828 | kWh |
| Powder Production | Argon | 2.58 | kg |
| Powder Production | Water | 0.116 | kg |
| SLM Build | Steel powder | 0.352 | kg |
| SLM Build | Electricity | 11.49 | kWh |
| SLM Build | Compressed air | 3.56 | m³ |
| SLM Build | Argon | 1.2 | m³ |
| Finish Machining | Electricity | 2.84 | kWh |
| Finish Machining | Cutting fluid | 1.94 | kg |
| Output | Marine propeller | 0.204 | kg |
| Waste | Machined chips | 0.116 | kg |

**Contextual Performance Metrics:**
- Gas atomization electricity intensity: 2 kWh/kg powder (calculated from process data)
- SLM build efficiency: 0.031 kg/h (based on 6.55 h build time)
- Machining material removal rate: 0.028 kg/h

---

## Equipment Status and Maintenance Notes

**SLM 280 HL Post-Build Check:**
- Recoater blade: No wear observed
- Optics: Clean, no contamination
- Filter unit: 15% life remaining
- Build plate: Minimal distortion, within tolerance

**CNC Mill VM-2 Post-Operation:**
- Tool holder: Secure
- Coolant system: No leaks
- Axis alignment: Within spec

No unscheduled maintenance required. All equipment is ready for next job.

---

## Comparative Data (Historical Reference)

*Note: The following data is for contextual comparison and is not part of the current build record.*

- **Previous similar build (Job SLM-2023-045):**  
  SLM electricity: ~12.1 kWh, Machining electricity: ~3.0 kWh  
  Powder usage: ~0.360 kg, Yield: ~0.200 kg

- **Industry benchmark for SLM of steel components:**  
  Typical electricity: 10-15 kWh per build, Powder efficiency: 80-90%

The current build showed improved powder utilization and slightly lower energy consumption compared to previous jobs, likely due to optimized support structures and laser parameters.

---

## Sign-off

**Operators:**  
J. Doe (SLM), R. Brown (Machining)  

**Quality Check:**  
Part dimensions and surface finish verified. No defects.

**Log Closed:** October 16, 2023, 14:00