# Calling-window map

`phone_mcp/area_codes.json` is a bundled, deliberately partial mapping of US geographic area codes to IANA timezone candidates. It is not a location lookup service. Unknown NPAs, toll-free numbers, and non-US numbers fail closed for calls. SMS has no time-window lookup.

For each candidate zone, Python `zoneinfo` converts the current UTC time using DST rules. Every candidate must be inside 08:00 inclusive to 21:00 exclusive. This intersection handles both the morning and evening edges for multi-zone NPAs. Some boundary regions intentionally use a conservative superset of zones. For example, 208 includes Pacific and Mountain; 850 includes Central and Eastern; 907 includes Anchorage and Adak. Arizona 928 includes Phoenix and Denver to account conservatively for differing DST observance.

Review new area-code assignments against [NANPA area-code maps](https://www.nanpa.com/resources/area-code-maps) and [NPA reports](https://www.nanpa.com/reports/npa-reports). Review timezone boundaries against [US Department of Transportation time-zone information](https://www.transportation.gov/regulations/time-act) and [IANA timezone data](https://www.iana.org/time-zones). These are maintenance references; the bundled mapping is a hand-maintained subset, not a synchronized NANPA database or an official timezone determination.

When adding an area code, include every plausible zone and add boundary tests. If uncertain, leave the code unsupported. Keep `tzdata` current. Portability and travel mean a phone number cannot establish the recipient's actual location. Verify that separately before live outreach; this guard cannot guarantee recipient-local compliance.
