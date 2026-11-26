"""Build a numtag writer block from CLDR RBNF rule sets (unicode-rbnf XML).

usage: cldr_writer.py XML OUT.json name=cldr-ruleset ... [--cardinal NAME] [--ordinal NAME] [--fem-cardinal NAME] [--fem-ordinal NAME]
"""
import json, re, sys, xml.etree.ElementTree as ET
xml, out, *args = sys.argv[1:]
pairs = dict(a.split("=", 1) for a in args if "=" in a and not a.startswith("--"))
roles = dict(a[2:].split(":", 1) for a in args if a.startswith("--"))
root = ET.parse(xml).getroot()
cldr = {rs.get("type"): rs for rs in root.iter("ruleset")}
rename = {v: k for k, v in pairs.items()}  # cldr name -> our name
rulesets = {}
for ours, theirs in pairs.items():
    rules = []
    for r in cldr[theirs].iter("rbnfrule"):
        value, text = r.get("value"), r.text
        if value in ("x.x", "x,x", "Inf", "NaN", "0.x", "x.0") or "#" in text:
            continue
        text = re.sub(r"%([\w-]+)", lambda m: "%" + rename[m.group(1)], text)
        rules.append({"value": value, "text": text})
    rulesets[ours] = {"source": f"CLDR RBNF {xml.rsplit('/', 1)[-1]} %{theirs}, without the decimal rules and the digit fallback", "rules": rules}
missing = {m for rs in rulesets.values() for r in rs["rules"] for m in re.findall(r"%([\w-]+)", r["text"])} - set(rulesets)
assert not missing, f"unmapped rule sets: {missing}"
def form(m, f):
    v = lambda n: [{"ruleset": n, "reason": "standard"}]
    spec = {"variants": v(m)}
    if f: spec["gender"] = {"masculine": v(m), "feminine": v(f)}
    return spec
forms = {"cardinal": form(roles["cardinal"], roles.get("fem-cardinal")), "ordinal": form(roles["ordinal"], roles.get("fem-ordinal"))}
if "masc-cardinal" in roles:
    forms["cardinal"]["gender"]["masculine"] = [{"ruleset": roles["masc-cardinal"], "reason": "standard"}]
json.dump({"writer": {"source": "CLDR RBNF " + xml.rsplit("/", 1)[-1], "rulesets": rulesets, "forms": forms}}, open(out, "w"), ensure_ascii=False, indent=1)
print(len(rulesets), "rule sets,", sum(len(r["rules"]) for r in rulesets.values()), "rules")
