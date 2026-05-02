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

**4. `Motors.acceleration` getter never queries the firmware**
`Motors.py:238` — The getter returns the cached `self._acceleration`
value, not the firmware's current acceleration.  If the firmware's
acceleration has been changed outside Python (e.g. a prior session
that did not restore settings), the Python cache diverges silently.
Resolution: document this limitation in the docstring, or add a
firmware read command (the Arduino protocol currently only *sets* `A`).

---

## Code duplication

**5. `RasterScan.trajectory` duplicates `Polargraph.i2r` inline**
`RasterScan.py:50-55` — The nested `i2r_vec` function is a NumPy-
vectorised copy of `Polargraph.i2r`.  It exists only because `i2r` uses
a scalar `if ysq >= 0` guard that breaks on arrays.
Resolution: replace the scalar guard in `Polargraph.i2r` with
`np.maximum(ysq, 0.)` so it vectorises naturally; delete `i2r_vec`
and call `pg.i2r` directly.

---

## API consistency

**6. Motion-state reported two ways via different serial commands**
`Motors.py:194` vs `Motors.py:208` — `running()` sends an `R` command;
`indexes` encodes the running flag as `indexes[2]` via the `P` command.
`_moveTo` polls `position[2]` (P-based); `main()` polls `running()` (R-based).
Sending both commands wastes round-trips and means callers must pick a path.
Resolution: document which path is authoritative and remove or deprecate
the other, or have `running()` delegate to `indexes[2]`.

**7. `_moveTo` result is a bare string instead of an enum**
`QScanPattern.py:233` — `_moveTo` returns `'complete'`, `'paused'`, or
`'abandoned'`.  These are used in six `if result ==` comparisons; a typo
is a silent logic error.
Resolution: add a small `_MoveResult` `StrEnum` or reuse/extend `ScanState`.

---

## Fragility

**8. `QScanPattern.rect`, `vertices`, and `trajectory` crash when `polargraph is None`**
`QScanPattern.py:164` — `rect` calls `self.polargraph.y0` without guarding.
`RasterScan` and `PolarScan` both call `self.rect` through `vertices()` and
`trajectory()`.  `TarzanScan` guards its geometry methods; the others don't.
Resolution: add `if self.polargraph is None: return ...` guards consistent
with `TarzanScan`, or raise a clear `RuntimeError`.

**9. `QScanner._SCAN_LOCKED` hardcodes widget attribute names**
`QScanner.py:97` — The tuple `('center', 'home', 'polargraph', 'scanner')`
must exactly match widget attribute names.  A subclass that renames or
adds locked widgets must also update this tuple; a mismatch fails silently
(the widget stays enabled when it should not).
Resolution: replace with a method `_lockedWidgets() -> list` that subclasses
can override explicitly.

---

## Test coverage gaps

**10. `QScanPattern._onMeasure` is untested**
Added in the latest feature commit; no test verifies that it is called in
the polling loop or that a subclass override is invoked.

**11. `QScanPattern.interruptAndClose` and `closeRequested` are untested**
These are critical for clean application shutdown; a regression here would
cause the app to hang on close.

**12. `QScanner._syncPatternThread` is untested**
The deferred-retry logic that moves the scan pattern to the device thread
is load-bearing for all real-hardware sessions.

**13. `RasterScan.trajectory` has no curvature test**
The whole point of the implementation is that it produces *curved* paths.
The existing tests verify shape and endpoints but not that the intermediate
points are non-collinear.

---

## Minor style / consistency

**14. `FakeMotors._acceleration` override needs a comment**
`fake.py:23` — `FakeMotors.__init__` resets `_acceleration` to zeros after
`super().__init__()` sets it to `[1000., 1000.]`.  The override is correct
(fake hardware does not simulate trapezoidal ramp dynamics) but looks like
an accidental reversion without a comment.

**15. `Motors.process` is a public no-op**
`Motors.py:159` — The method exists as a base-class hook but does nothing
and has no documented contract for subclasses.  It shadows the parent's
`process()` without adding behaviour.
Resolution: remove it or make it private and document the override contract.

**16. `main()` utilities embedded in library modules**
`Motors.py:251`, `Polargraph.py:284` — Standalone driver scripts inside
importable modules are unconventional and inflate the module's public
footprint.
Resolution: move to `examples/` or guard under `if __name__ == '__main__'`
only (already done) with a note in the docstring that these are dev-only.
