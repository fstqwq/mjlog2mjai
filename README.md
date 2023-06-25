# Tenhou mjlog to MJAI Event Json

Convert [Tenhou MJLOG XML](https://tenhou.net/6/) to [MJAI Json](https://github.com/gimite/mjai) format directly, instead of querying `https://tenhou.net/5/mjlog2json.cgi?{log_id}` slowly.


## Usage

```python
from .parse import load_mjlog, parse_mjlog_to_mjai
mjai_data = parse_mjlog_to_mjai(load_mjlog("xx.mjlog"))
```

## Compatibility and known issues

Checked on ~2000 games, mostly matched with [mjai-reviewer](https://github.com/Equim-chan/mjai-reviewer). See `test.py`, where `check/` contains the tenhou official site [unzipped file](https://tenhou.net/0/log/mjlog_pf4-20_n17.zip).

The only differences are kakans with akari dora: the order they appeared in `consumed` field is decided by `mjlog2json.cgi` and seems arbitrary (or I didn't understand the encoding correctly),
so I left it unfixed.

## Acknowledgement

Parser was originally from [tenhou-log-utils](https://github.com/mthrok/tenhou-log-utils). Hence this repository is also under the MIT license.