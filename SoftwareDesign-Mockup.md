### based on: **`dustcollector_fixpoint9_logging_and_design_20251226`**
---

# DustCollector Controller – Software Design

## 1. What this system actually does (plain English)

This system watches your woodworking machines and automatically:

- Turns the **dust collector motor ON** when _any_ machine starts
    
- Opens the **correct blast gate(s)** for the running machine(s)
    
- Closes gates when machines stop
    
- Turns the dust collector OFF when **all machines are idle**
    
- Does this safely even if multiple machines start/stop close together
    
- Adds optional “fun” outputs (LEDs, displays, sounds) without affecting core behavior
    

Everything else in the code exists to support that simple goal **reliably**.

---

## 2. The core idea: events, not commands

Nothing directly tells anything else _what to do_.

Instead:

- Parts of the system **publish events**
    
- Other parts **react to events**
    

Think of it like shop chatter:

> “Hey, the lathe just turned on.”  
> “Okay, then I’ll open the lathe gate.”  
> “Also, I’ll start the dust collector.”

This avoids tight coupling and timing bugs.

---

## 3. The EventBus (the nervous system)

At the center is the **EventBus**.

- Any task can **publish** an event
    
- Any task can **subscribe** and receive events
    
- All subscribers get all events (broadcast model)
    

### Important property

The EventBus is **not** pub/sub by topic.  
It is **broadcast + local filtering**.

Each task says:

> “I’ll listen to everything, but I only care about X.”

This keeps the bus simple and predictable.

---

## 4. The main tasks (who does what)

### 4.1 `adc_watch` – machine detection

**Responsibility:**

- Periodically read ADC channels
    
- Decide if each machine is ON or OFF
    
- Publish:
    
    - `machine.on:<name>`
        
    - `machine.off:<name>`
        

**Key design choice:**

- Debouncing and thresholds live _here_
    
- Everyone else gets clean, meaningful state changes
    

This isolates noisy analog behavior.

---

### 4.2 `machine_manager` – state authority

**Responsibility:**

- Track which machines are currently ON
    
- Publish higher-level events:
    
    - `collector.on`
        
    - `collector.off`
        

**Why it exists:**

- The dust collector should not turn off just because _one_ machine stopped
    
- This component answers the question:
    
    > “Is _any_ machine still running?”
    

It is the **single source of truth** for machine state.

---

### 4.3 `gate_controller` – blast gates

**Responsibility:**

- Open a gate when its machine turns ON
    
- Close a gate when its machine turns OFF
    

**Concurrency rule (important):**

- Each gate has its **own lock**
    
- Writes to the relay bank are **atomic masked updates**
    

This means:

- Two gates can move at the same time
    
- No gate blocks another unnecessarily
    
- The relay state is never corrupted by partial writes
    

This directly addresses your “two people, two machines” scenario.

---

### 4.4 `collector_controller` – dust collector motor

**Responsibility:**

- Turn the dust collector motor ON/OFF via SSR
    
- React only to:
    
    - `collector.on`
        
    - `collector.off`
        

**Design constraint:**

- It does _not_ care which machine triggered the event
    
- It only cares whether the system needs suction or not
    

That simplicity is intentional and protective.

---

### 4.5 Optional / non-critical tasks

These listen but do not control core behavior:

- `pms1003` – air quality monitoring
    
- `display_status` – LCD/OLED output
    
- `funhouse` – LEDs, sounds, amusement
    
- `sys_monitor` – Pi temperature, enclosure fan
    

If any of these fail, **dust collection still works**.

That is a deliberate safety boundary.

---

## 5. Hardware abstraction (why mocks work)

Every hardware interaction is behind a **small, stable interface**.

Example: GPIO output

```python
class GPIOOutLike(Protocol):
    def write(self, on: bool) -> None: ...
```

Both:

- `GPIOOut` (real hardware)
    
- `MockGPIOOut` (laptop testing)
    

implement the **same interface**.

Tasks never ask:

> “Are we mocked?”

They just say:

> “Turn this on.”

This is why you can run the whole system on your laptop.

---

## 6. Why mypy matters here

mypy is doing one job for us:

> **Prevent silent interface drift.**

If a mock and real device disagree:

- Constructor arguments
    
- Methods available
    
- Return types
    

mypy stops the system _before runtime_.

The long struggle we just went through was **locking those contracts down**.  
Now that they’re stable, progress becomes fast again.

---

## 7. Startup sequence (what happens on boot)

1. `main.py` loads configuration
    
2. Hardware layer initializes (real or mock)
    
3. EventBus is created
    
4. Tasks are started concurrently:
    
    - ADC watcher
        
    - Machine manager
        
    - Gate controller
        
    - Collector controller
        
    - Optional display/fun tasks
        
5. System idles until events occur
    

Nothing moves unless something _changes_.

---

## 8. Why this design is robust

- No global locks
    
- No long-held mutexes
    
- No task blocks another unnecessarily
    
- All time-dependent behavior is local
    
- All hardware writes are controlled and atomic
    
- Failure in “fun” code does not affect safety
    

This is **industrial control logic**, not hobby spaghetti.

---

## 9. Mental model to keep in your head

If you remember only one thing, remember this:

> **Sensors produce events.  
> Managers interpret events.  
> Actuators react to events.**

Nothing else reaches across layers.

---
