# QPolargraph — development TODO

Items are ordered roughly by impact.  Each entry names the file and
approximate line, describes the problem, and sketches a resolution.

---

## Type-hint errors

**1. `r2f` and `r2i` have invalid return annotations**
`Polargraph.py:175,200` — `-> tuple(float, float)` and `-> tuple(int, int)` are
runtime *calls*, not annotations.  Python evaluates them eagerly and silently
stores the result; mypy and IDEs never see the intended type.
Resolution: `-> tuple[float, float]` and `-> tuple[int, int]`.

**2. `i2r` return annotation is imprecise**
`Polargraph.py:217` — `i2r(m, n, *args) -> np.ndarray` appends `*args`
to the result, so the return length is caller-determined.  The `*args`
pass-through is intentional: `position` calls `i2r(*self.indexes)` to
carry the running flag without a separate field.  The annotation
`-> np.ndarray` is accurate but conveys nothing about the shape.
Resolution (optional): add a docstring note that `len(result) == 2 + len(args)`
and that callers control the payload via `*args`.

---

## Documentation / units

**3. `speed` property documented as mm/s, used as steps/s** ✓ fixed
`Polargraph.py` docstrings updated to `[steps/s]`; widget suffix was already correct.

**4. `Motors.acceleration` getter never queries the firmware** ✓ fixed
Docstring updated to explain the cache-only behaviour and firmware default.

---

## Code duplication

**5. `RasterScan.trajectory` duplicates `Polargraph.i2r` inline** ✓ fixed
`i2r` now uses `np.maximum(ysq, 0.)` and `np.any(ysq < 0)` for the
error guard, making it work with scalar or array inputs.  `i2r_vec`
deleted; `RasterScan.trajectory` calls `pg.i2r` directly.

---

## API consistency

**6. Motion-state reported two ways via different serial commands** ✓ fixed
`running()` now delegates to `indexes[2]` (P command), consistent with
the scan loop.  Firmware R command preserved for direct hardware use.

**7. `_moveTo` result is a bare string instead of an enum** ✓ fixed
`_MoveResult(Enum)` with `COMPLETE/PAUSED/ABANDONED` added to
`QScanPattern.py`; all six comparison sites updated.

---

## Fragility

**8. `QScanPattern.rect`, `vertices`, and `trajectory` crash when `polargraph is None`** ✓ fixed
`polargraph` is now a required parameter (no `None` default).
`QScanner.setupScanner` constructs the pattern with polargraph in one step.
`QScanPatternWidget` no longer creates a default `PolarScan()` without hardware.
All `polargraph is None` guards in `TarzanScan` removed.

**9. `QScanner._SCAN_LOCKED` hardcodes widget attribute names** ✓ fixed
Replaced with `_lockedWidgets() -> list`; subclasses extend via
`super()._lockedWidgets() + [self.my_widget]`.

---

## Test coverage gaps

**10. `QScanPattern._onMeasure` is untested** ✓ fixed
`test_onMeasure_subclass_override_called_during_scan` verifies the override
is invoked with correct ``(t, x, y)`` types during a scan.

**11. `QScanPattern.interruptAndClose` and `closeRequested` are untested** ✓ fixed
Three tests cover: IDLE → immediate emit, PAUSED → cleanup + emit,
SCANNING → abandon + emit.

**12. `QScanner._syncPatternThread` is untested** ✓ fixed
Three tests: no-op for fake device, no-op when device on main thread,
and pattern moved when device is on a worker thread.

**13. `RasterScan.trajectory` has no curvature test** ✓ fixed
`test_raster_trajectory_is_curved` asserts midpoint deviation > 1e-6 m
from the straight-line chord.

---

## Minor style / consistency

**14. `FakeMotors._acceleration` override needs a comment** ✓ fixed
Added inline comment: 'Zero acceleration: fake hardware moves at constant
speed, no ramp.'

**15. `Motors.process` is a public no-op** ✓ fixed
Added NumPy-style docstring explaining it logs unsolicited serial data and
documents the subclass override contract.

**16. `main()` utilities embedded in library modules** ✓ fixed
Added one-line docstring to both `Motors.main()` and `Polargraph.main()`
marking them as dev-only smoke tests.
