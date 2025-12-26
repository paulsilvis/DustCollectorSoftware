### 1. Why the current EventBus is fine for DustCollectorSoftware

- `N_machines <= ~12`  
    → Even if you end up with 1–2 handlers per machine plus a few global ones, you’re still in the “dozens of handlers” regime, not hundreds.
    
- Event rate is bounded by physics  
    → Humans turning machines on/off, some timers, sensor edges.  
    You’re not doing market data or a game engine at 10 kHz.
    
- Pi performance is **orders of magnitude** above what you need  
    → Even a fairly dumb “send every event to every handler” will be noise compared to I/O, logging, and Python itself.
    

From a **performance** perspective, you’re not going to hit the O(N_handlers) wall with this shop system. You’ll retire before the bus does.

So: for this project, _as long as it stays in the same conceptual size class_, broadcast + local filtering is not going to melt the Pi.

---

### 2. Where it _could_ start to hurt (for you specifically)

Even at small scale, the failure mode is **not speed**, it’s **clarity**:

- If you later pile more “cute” subsystems on the same bus  
    (LED airflow show, Plantower air monitor, LoRa status, future toys),  
    you can end up with a lot of handlers all listening to the same flood of “system-ish” events.
    
- If handlers start to become mini-routers:
    
    ```python
    async def on_event(ev: Event) -> None:
        if isinstance(ev, SawStarted): ...
        elif isinstance(ev, LatheStarted): ...
        elif isinstance(ev, GateTimedOut): ...
        elif isinstance(ev, LedEffectRequested): ...
        # etc
    ```
    
    that’s a smell. Now the topology is implicit and hard to reason about.
    
- If you ever find yourself asking “who the hell reacts to `GateOpened`?” and needing `rg`/`grep` to understand the system, the broadcast model is starting to push back.
    

You’re safe now. Just don’t let it quietly drift into that pattern without noticing.

---

### 3. Simple guardrails so broadcast stays sane

You can keep the core design **and** protect yourself with a few rules:

- **One handler = one narrow concern**  
    No god-handlers. A handler should care about a small set of event types.
    
- **Strongly typed events**  
    Dataclasses / simple classes, not loose dicts. Filtering should be cheap:
    
    ```python
    if not isinstance(ev, ToolEvent):
        return
    ```
    
- **Multiple buses if needed**  
    If/when you add serious side projects (LED shows, LoRa telemetry), give them their own bus instead of stuffing everything into `CoreBus`.
    
- **Self-diagnostics**  
    Later, if you’re worried, add a tiny counter:
    
    - events/sec
        
    - total dispatches/sec  
        That’ll tell you if the bus is becoming hot.
        

---

### 4. Bottom line

- For the dust collector as you’ve defined it:  
    **broadcast + local filtering is absolutely fine long-term.**
    
- If the system later grows into “Pi as general shop control OS,”  
    the first sign it’s time to refactor won’t be CPU usage, it’ll be you swearing at scattered `if isinstance(...)` chains.
    

Until then, leave it simple and get real hardware running. If we ever hit the point where the bus is in your way, switching to a minimal topic/typed model is a local refactor, not a rewrite.

/Bob