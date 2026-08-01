# Walking-skeleton specification

## Scientific scenario

The final report states:

> Treatment increased expression relative to control.

The linked saved result is a scalar coefficient. The detector compares the report direction only after normalizing the coefficient into the report's treated-versus-control orientation.

## Cases

### Positive synthetic case

```text
report direction: positive
stored value: -0.42
stored orientation: treated minus control
normalized direction: negative
expected: one fixture-only Finding
```

### Hard negative

```text
report direction: positive
stored value: -0.42
stored orientation: control minus treated
normalized value: +0.42
expected: no Finding
```

### Material unknown

```text
report direction: positive
stored value: -0.42
stored orientation: unknown
expected: orientation question; no Finding
```

The base demo also retains a separate question about what `sample_id` identifies. That question illustrates that unrelated scientific ambiguity can coexist with a demonstrated report/result contradiction.

## Opaque boundary

`workflow.sh` invokes `opaque-normalizer`. The auditor does not execute or interpret that tool. It records a Disclosure while allowing the report/result detector to operate on the locked downstream scalar.

## Test-double rule

The bundled detector is marked as validated only inside an explicitly marked synthetic fixture envelope so the admission machinery can be exercised. `sc-referee demo` and `replay` reject locks without `fixture_mode: true`. No public detector qualification is claimed.
