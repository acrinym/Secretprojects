# TECHNICAL ARCHITECTURE & IMPLEMENTATION
## Power Over Bluetooth: From Physics to Product

---

## PHYSICS FUNDAMENTALS

### The Power Budget Challenge

**Conventional Bluetooth Power Levels:**
```
Class 1 (100mW, 20dBm): Long range devices, rare
Class 2 (2.5mW, 4dBm): Most smartphones, common
Class 3 (1mW, 0dBm): Short range devices
```

**Free Space Path Loss (Friis Equation):**
```
Pr = Pt × Gt × Gr × (λ/4πd)²

Where:
- Pr = Received power
- Pt = Transmitted power  
- Gt/Gr = Transmit/Receive antenna gains
- λ = Wavelength (12.5cm at 2.4GHz)
- d = Distance

At 1 meter with typical antennas:
- Path loss ≈ 40dB
- Class 2 phone (2.5mW) → 0.025μW received
```

**The Brutal Truth**: Standard far-field approach yields 25 nanowatts at 1 meter. Not viable.

---

## BREAKTHROUGH ARCHITECTURE 1: NEAR-FIELD POWER COUPLING

### Physics of Near-Field
In reactive near-field (d < λ/2π ≈ 2cm for 2.4GHz), power coupling follows **different physics**:
- Energy oscillates between transmitter and receiver (evanescent waves)
- Does NOT radiate into far field
- Inverse distance decay (d⁻³) not inverse square (d⁻²) at very close range
- 10-100x better efficiency than far-field at <5cm

### Technical Implementation

**Transmitter Design (Phone Case):**
```
Component Stack:
1. NFC-style resonant loop antenna (40mm diameter)
2. Class-E RF amplifier (90% efficient)  
3. Bluetooth 2.4GHz carrier
4. Power management IC (TI bq500410 or similar)
5. Thin-film battery for buffering

Specifications:
- Output power: 100mW (within FCC limits for non-radiating near-field)
- Efficiency: 70-80% phone battery → RF
- Coupling distance: <10cm optimal, <15cm functional
```

**Receiver Design (Wearable Device):**
```
Component Stack:
1. Tuned receive loop (25mm diameter)
2. Impedance matching network
3. Schottky diode rectifier bridge
4. Energy harvesting IC (e-peas AEM10941)
5. Storage capacitor (10mF supercap)
6. Load (sensor + BLE transmitter)

Specifications:
- Received power at 3cm: 1-10mW
- Rectification efficiency: 60-75%
- Usable DC power: 0.6-7.5mW
- Sufficient for: Glucose sensors, accelerometers, temperature sensors, e-ink displays
```

**Key Innovation**: This is NOT far-field radiation, so FCC power limits for intentional radiators don't apply. Operates under Part 15 unintentional radiator rules.

### Target Applications
- Smart rings that charge when near phone
- Glucose monitor patches that charge during sleep (phone on nightstand)
- Smart watch charging while wearing (phone in pocket <10cm away)
- Medical sensors that live on phone case permanently

---

## BREAKTHROUGH ARCHITECTURE 2: AMBIENT BACKSCATTER

### Physics of Backscatter Communication

**Principle**: Device doesn't generate RF power - it modulates existing ambient signals by switching antenna load impedance.

**Power Budget:**
```
Ambient Bluetooth power: -20 to -10dBm (10-100μW)
Backscatter reflection: -40 to -30dBm (0.1-1μW received by phone)
Device power consumption: 100-500nW (ultra-low power ASIC)

Energy available: 10-100μW
Energy required: 0.1-0.5μW
Margin: 20-1000x surplus
```

### Technical Implementation

**Backscatter Tag (Sensor Device):**
```
Component Stack:
1. Dipole antenna (2.4GHz resonant)
2. Switch-based modulator (PIN diode or FET)
3. Ultra-low-power MCU (Ambiq Apollo, <1μA active)
4. Sensor (temperature, accelerometer, etc.)
5. Small storage capacitor

Operation:
- Harvest ambient Bluetooth to charge capacitor
- When threshold reached, activate
- Read sensor
- Modulate antenna impedance to send data
- Return to sleep

Power profile:
- Sleep: 50nA
- Active: 3μA (1ms burst)
- Average: <200nA
```

**Reader Modification (Smartphone):**
```
Software stack:
- Modified Bluetooth firmware (read backscatter modulation)
- Signal processing to detect amplitude modulation
- Error correction for low SNR signals

Hardware:
- No modification required (standard Bluetooth radio)
- Software-defined radio approach
```

### Key Innovation
This eliminates the "power transmission" problem entirely. Devices are **purely parasitic** on existing RF infrastructure.

### Target Applications
- Asset tracking tags (warehouse, retail)
- Environmental sensors (temperature, humidity, CO2)
- Smart home sensors (door/window, motion)
- Inventory management (retail stockroom)

---

## BREAKTHROUGH ARCHITECTURE 3: DISTRIBUTED COHERENT BEAMFORMING

### Physics of Constructive Interference

**Principle**: Multiple Bluetooth transmitters coordinate phase to create constructive interference at target location.

**Power Gain:**
```
N coherent sources → N² power gain at target
3 sources → 9x power (9.5dB gain)
4 sources → 16x power (12dB gain)
10 sources → 100x power (20dB gain)

Example:
- 3 phones each transmitting 2.5mW
- Without coordination: 2.5mW average at target
- With phase coordination: 22.5mW at target (9x gain)
```

### Technical Implementation

**Coordination Protocol:**
```
System Components:
1. Master coordinator (one phone or dedicated hub)
2. Slave transmitters (other phones, laptops, speakers)
3. Target device (sensor reporting location)
4. Feedback mechanism (power level sensing)

Algorithm:
1. Target device broadcasts location beacon
2. Master coordinator calculates phase offsets for each transmitter
3. Transmitters adjust phase to create constructive interference at target
4. Target measures received power, reports back
5. System adapts in real-time (feedback loop)

Challenges:
- Phase synchronization (<1ns timing accuracy required)
- Position estimation (location of all devices)
- Mobility handling (update rates 10-100Hz)
```

**Implementation Approach:**

**Phase 1 - Static Network:**
```
Scenario: Fixed beacons in building
- Wall-mounted Bluetooth beacons (3-6 per room)
- Known positions (surveyed during install)
- Wired power available
- Central controller coordinates phases

Performance:
- 10-20x power delivery improvement
- Static targets (sensors at known locations)
- 99%+ uptime
```

**Phase 2 - Mobile Network:**
```
Scenario: Phones coordinate dynamically
- Uses UWB positioning for phone locations
- Peer-to-peer phase coordination protocol
- Software update to enable coordination mode
- Opt-in for users (phone acts as power beacon when idle)

Performance:
- 5-10x power improvement (less precise than static)
- Dynamic adaptation as phones move
- Works for mobile wearables
```

### Key Innovation
Leverages **existing installed base** of Bluetooth devices. Network effect: More devices = better power coverage.

### Target Applications
- Commercial building sensor networks
- Smart home with multiple Bluetooth sources
- Retail environments (smartphones + beacons)
- Hospitals (equipment tracking, patient monitoring)

---

## BREAKTHROUGH ARCHITECTURE 4: METAMATERIAL RF CONCENTRATORS

### Physics of Metamaterial Focusing

**Principle**: Engineered structures with negative refractive index can focus electromagnetic waves beyond diffraction limit.

**Conventional Limit:**
```
Minimum spot size ≈ λ/2 ≈ 6cm at 2.4GHz
```

**Metamaterial Enhancement:**
```
Sub-wavelength focusing: λ/10 possible
Spot size: 1-2cm
Power concentration: 10-100x in focal region
```

### Technical Implementation

**Metamaterial Lens Design:**
```
Physical Structure:
- Printed circuit board with copper patterns
- Split-ring resonators (SRRs) at 2.4GHz resonance
- Multiple layers (3-5) for focusing
- Total thickness: 5-10mm
- Form factor: Wearable patch or phone case addition

Electromagnetic Properties:
- Effective permittivity: εeff < 0
- Effective permeability: μeff < 0  
- Focusing gain: 10-20dB (10-100x)
- Bandwidth: 2.3-2.5GHz (covers Bluetooth + WiFi)

Manufacturing:
- Standard PCB fabrication
- Cost: $2-5 per unit at scale
- No active components (entirely passive)
```

**System Integration:**
```
Wearable Configuration:
1. Metamaterial lens (worn on arm, chest, or head)
2. Receiver antenna at focal point
3. Energy harvesting IC
4. Load device (sensor, display, transmitter)

Performance:
- Ambient power without lens: 10nW - 1μW
- Ambient power WITH lens: 100nW - 100μW  
- Enables orders of magnitude more functionality
```

### Key Innovation
**Passive amplification** of ambient RF. User wears "RF glasses" that focus electromagnetic energy. No battery, no active electronics in the lens itself.

### Target Applications
- Medical monitoring patches (continuous glucose, heart rate)
- Smart badges (conference name tags, security access)
- Wearable displays (e-ink information displays)
- Fitness tracking sensors

---

## BREAKTHROUGH ARCHITECTURE 5: ULTRA-CAPACITOR TIME-SHIFTING

### Physics of Energy Accumulation

**Principle**: Harvest microwatts continuously, store in ultra-capacitor, discharge in millisecond bursts for high-power operations.

**Power Budget:**
```
Continuous harvesting: 10μW average
Accumulation time: 100 seconds
Energy stored: 10μW × 100s = 1000μJ = 1mJ

Burst discharge: 1mJ in 1 second = 1mW average power
Sufficient for: Full BLE transmission (0dBm, 1mW)

Duty cycle: 1% (1s transmit per 100s accumulate)
Effective power: 100x multiplication
```

### Technical Implementation

**Energy Storage System:**
```
Component Selection:
1. Ultra-capacitor: 
   - Capacitance: 1-10mF
   - Voltage: 3-5V
   - Leakage: <1μA
   - Size: 5-10mm diameter
   - Cost: $0.50-2.00

2. Energy Harvesting IC (e-peas AEM10941):
   - Cold-start voltage: 380mV
   - MPPT (maximum power point tracking)
   - Programmable output voltage
   - <1μA quiescent current

3. Burst Controller:
   - Voltage threshold monitoring
   - Wake-on-threshold circuit
   - Power gating for load
```

**Operation Sequence:**
```
Phase 1 - Accumulation (99% of time):
- Harvest RF energy at 10-100μW rate
- Store in ultra-capacitor
- Monitor voltage with nA-level comparator
- Load completely powered off

Phase 2 - Burst Operation (1% of time):
- Capacitor reaches threshold (e.g. 3.3V)
- Controller wakes load
- Sensor reads data
- BLE transmitter sends packet (1-10ms)
- Return to accumulation phase

Timing examples:
- 10μW harvest, 1mJ storage: 100s cycle
- 50μW harvest, 1mJ storage: 20s cycle  
- 100μW harvest, 5mJ storage: 50s cycle
```

### Key Innovation
**Time arbitrage**: Convert low-power continuous into high-power intermittent. Enables using standard BLE protocols at full power from ultra-low harvested power.

### Target Applications
- Environmental sensors (temperature, humidity every minute)
- Asset tracking (location report every 30 seconds)
- Security sensors (door/window status every 10 seconds)
- Industrial monitoring (vibration snapshot every minute)

---

## BREAKTHROUGH ARCHITECTURE 6: HYBRID MULTI-SOURCE HARVESTING

### Physics of Energy Portfolio

**Principle**: Combine RF with complementary energy sources to ensure 24/7 availability.

**Energy Source Characteristics:**
```
RF (Bluetooth):
- Available: 24/7 indoors and outdoors
- Power level: 10-1000μW depending on proximity
- Weather independent
- Requires nearby transmitters

Solar (Indoor lighting):
- Available: Daytime with lights on
- Power level: 100-10,000μW depending on illumination
- Weather/location dependent
- No infrastructure required

Kinetic (Motion):
- Available: During movement
- Power level: 100-5000μW depending on activity
- Intermittent (sedentary periods)
- No infrastructure required

Thermal (Body heat):
- Available: 24/7 when worn
- Power level: 10-100μW (small ΔT)
- Continuous but low
- Requires skin contact
```

### Technical Implementation

**Hybrid Architecture:**
```
System Design:
1. Multiple input channels:
   - RF rectenna circuit
   - Solar cell array
   - Piezoelectric or electromagnetic kinetic harvester
   - Optional: thermoelectric generator

2. Power management IC (TI BQ25570 or e-peas AEM30xxx):
   - Multiple input MPPT
   - Input prioritization logic
   - Battery/supercap charging
   - Load power gating

3. Energy storage:
   - Small rechargeable battery (10-50mAh) OR
   - Large supercapacitor bank (100mF+)

4. Load device:
   - Ultra-low-power MCU
   - Sensors
   - BLE transmitter
   - Optional: E-ink display
```

**Energy Complementarity:**
```
Scenario 1 - Fitness Tracker:
- Daytime walking: Kinetic (primary) + Solar (secondary)
- Daytime stationary: Solar (primary) + RF (secondary)  
- Nighttime walking: Kinetic (primary) + RF (secondary)
- Nighttime stationary: RF (primary) + Thermal (secondary)
→ Result: 24/7 operation without external charging

Scenario 2 - Smart Watch:
- Office worker: RF (primary, phone nearby) + Indoor solar (secondary)
- Outdoor athlete: Solar (primary) + Kinetic (secondary)
- Evening couch: RF (primary, TV/phone nearby) + Thermal (secondary)
→ Result: Never needs wall charging

Scenario 3 - Smart Home Sensor:
- Window placement: Solar (primary) + RF (backup)
- Interior placement: RF (primary) only
- Battery/supercap provides 30+ day backup for RF outage
→ Result: "Install and forget" sensor (no battery replacement)
```

### Key Innovation
**Energy portfolio diversification**. Like investment portfolio - low correlation between sources ensures consistent availability.

### Target Applications
- Fitness trackers & smartwatches (eliminate charging ritual)
- Smart home sensors (eliminate battery replacement)
- Medical wearables (continuous monitoring without charging anxiety)
- E-ink displays (always-on information displays)

---

## COMPONENT ECOSYSTEM

### Energy Harvesting ICs (Commercial, Available Today)

**e-peas AEM Family:**
```
AEM10941:
- Input: 100μW - 100mW
- Cold-start: 380mV
- Efficiency: 80-90%
- Features: MPPT, programmable Vout
- Cost: $2-3 in volume

AEM30940:  
- Triple input (solar, thermal, vibration)
- Input: 1μW - 100mW
- Features: Input prioritization, MPPT per input
- Cost: $4-6 in volume
```

**Texas Instruments BQ25570/BQ25504:**
```
BQ25570:
- Input: 10μW - 10mW
- Cold-start: 330mV (with boost)
- Efficiency: 80-92%
- Features: Nano-power, MPPT, programmable
- Cost: $1.50-2.50 in volume
```

**Powercast P21XXCSREVB:**
```
Complete reference design:
- RF input: -20dBm to +20dBm
- DC output: 3.3V or 5V
- Efficiency: 30-60% (RF to DC)
- Cost: $10-15 (reference board)
```

### Ultra-Low-Power MCUs

**Ambiq Apollo Series:**
```
Apollo4:
- Active: 5μA/MHz (100x better than competitors)
- Sleep: 2.4μA
- Deep sleep: 140nA
- Features: ARM Cortex-M4, BLE 5
- Cost: $2-4 in volume
```

**Nordic nRF52 Series:**
```
nRF52832:
- Active: 8μA/MHz  
- Sleep: 2μA
- Features: BLE 5, ARM Cortex-M4
- Ecosystem: Excellent SDK, support
- Cost: $2-3 in volume
```

**Texas Instruments CC1352:**
```
CC1352P:
- Sub-GHz + 2.4GHz dual-band
- Active: 6.5μA/MHz
- Sleep: 1μA
- Features: Sensor controller (autonomous)
- Cost: $3-5 in volume
```

### Energy Storage

**Supercapacitors:**
```
CAP-XX HS Series:
- 90-600mF range
- Thin form factor (0.9mm)
- Low ESR (0.1-0.5Ω)
- Cost: $1-3 in volume

Murata DMF Series:
- 10-100mF range
- Ultra-low leakage (<50nA)
- Cost: $0.50-1.50 in volume
```

**Thin-Film Batteries:**
```
Cymbet EnerChip:
- 50-740μAh capacity
- Rechargeable (5000+ cycles)
- Thin profile (1.5mm)
- Cost: $3-8 in volume
```

---

## PROTOTYPE ROADMAP

### Phase 1: Near-Field Demonstrator (Months 1-3)
**Goal**: Prove near-field coupling efficiency at 2.4GHz

```
Hardware:
- Phone case transmitter (Class-E amp + loop antenna)
- Smart ring receiver (small loop + rectifier)
- Power measurement instrumentation

Success Criteria:
- >1mW delivered at 5cm distance
- >50% end-to-end efficiency
- Operate within FCC Part 15 limits

Estimated Cost: $5,000
```

### Phase 2: Backscatter Sensor (Months 4-6)
**Goal**: Demonstrate battery-free sensor communication

```
Hardware:
- Backscatter tag (antenna + modulator + Ambiq MCU + sensor)
- Modified smartphone reader (software update to detect backscatter)

Success Criteria:
- 100% passive operation (no battery)
- 3-meter range
- 1kbps data rate minimum

Estimated Cost: $10,000
```

### Phase 3: Hybrid Harvester (Months 7-9)
**Goal**: Multi-source energy collection for 24/7 operation

```
Hardware:
- Smart watch form factor
- Solar + RF + Kinetic harvesting
- e-peas AEM30940 power management
- Nordic nRF52 + sensors + e-ink display

Success Criteria:
- 7 days continuous operation (no external charging)
- Demonstrate complementarity of energy sources
- Wearable-acceptable form factor

Estimated Cost: $25,000
```

### Phase 4: Distributed Beamforming (Months 10-12)
**Goal**: Coordinated power delivery from multiple sources

```
Hardware:
- 4x Bluetooth beacons (custom hardware with phase control)
- Central coordinator (Raspberry Pi or similar)
- Test sensor node with power measurement

Success Criteria:
- 10x power delivery improvement vs single source
- Real-time adaptation to position changes
- <100ms convergence time

Estimated Cost: $15,000
```

---

## TOTAL ESTIMATED PROTOTYPE COSTS: $55,000

---

## MANUFACTURING CONSIDERATIONS

### Bill of Materials (Smart Watch Example)

**At Volume (100,000 units):**
```
Component                        Cost
─────────────────────────────────────────
PCB (4-layer, RF-optimized)     $2.50
Energy Harvesting IC (e-peas)   $3.00
MCU (Nordic nRF52)              $2.50
Solar cells (thin-film)         $1.50
Piezo harvester                 $0.80
RF antenna (integrated PCB)     $0.30
Supercapitor (100mF)           $1.20
Sensors (accel, HR, temp)       $2.50
E-ink display (optional)        $5.00
Case + assembly                 $4.00
─────────────────────────────────────────
Total BOM                       $23.30

Manufacturing (assembly, test)   $6.70
Amortized NRE (tooling)         $2.00
─────────────────────────────────────────
Landed Cost                     $32.00

Target Retail                   $149-199
Margin                          78-84%
```

### Manufacturing Partners

**Contract Manufacturers:**
- **Flex** (formerly Flextronics): High-volume consumer electronics
- **Jabil**: Wearables experience
- **Sanmina**: Medical device experience (regulatory knowledge)

**PCBA Specialists:**
- **RUSH PCB**: RF-optimized boards, prototyping
- **Sierra Circuits**: HDI, impedance-controlled boards

---

## NEXT DOCUMENT: Market Strategy & Go-to-Market Plan
