# xeno-lvb

A tool to extract gimmick disposition files (`.lvb`) from Xenoblade 2 and 3.

## Usage

```
python xeno_lvb.py [command] (arg) [path to .lvb file]
```

Available commands:

* `full`: dumps the lvb file as JSON to standard output.
* `gimmick`: dumps gimmick data as JSON to standard output. The gimmick is matched by hash ID (XC3) or name (XC2), `arg` is the value to match.
  * For XC3, hash IDs can be entered as `<8 hex digits>`, e.g. `<123456AB>`
* `bdat`: dumps gimmick data as JSON to standard output. The gimmick is matched by its hashed BDAT ID. (`arg`, XC3 only)

## Extending

By default, the tool dumps all unknown gimmick types as hex byte strings.

Gimmick structure definitions can be added to the respective Python modules:

* For enemy gimmicks, `lvb_[game]_enemy.py` (e.g. `lvb_xc3_enemy.py`).
* For field gimmicks, `lvb_[game]_field.py`.
* For other or uncertain gimmick types, `lvb_[game]_other.py`.
