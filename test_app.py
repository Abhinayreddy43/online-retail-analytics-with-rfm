from streamlit.testing.v1 import AppTest
import pandas as pd, sys

def errs(at):
    return [e.value for e in at.exception]

# ---------- Page 1
at = AppTest.from_file("views/overview.py", default_timeout=120).run()
print("P1 default exceptions:", errs(at)); assert not at.exception
print("  metrics html cards:", sum('class="kpi"' in m.value for m in at.markdown))
for opt in ["United Kingdom", "International", "All"]:
    at.sidebar.radio[0].set_value(opt).run()
    print("  market", opt, "exceptions:", errs(at)); assert not at.exception
at.sidebar.select_slider[0].set_value(("2011-01", "2011-06")).run()
print("  period 2011-01..06 exceptions:", errs(at)); assert not at.exception
at.sidebar.select_slider[0].set_value(("2011-12", "2011-12")).run()
print("  single partial month exceptions:", errs(at)); assert not at.exception
at.sidebar.select_slider[0].set_value(("2010-12", "2011-12")).run()
for r in ["Revenue", "Units sold", "Orders (popularity)"]:
    rank = next(x for x in at.radio if x.label == "Rank by")
    rank.set_value(r).run(); assert not at.exception, errs(at)
print("  product ranking metrics OK")

# ---------- Page 2
at = AppTest.from_file("views/customers.py", default_timeout=120).run()
print("P2 default exceptions:", errs(at)); assert not at.exception
rfm = pd.read_parquet("data/rfm.parquet")
sel = at.selectbox[0]
opts = list(sel.options)
print("  dropdown options:", len(opts), "| first:", opts[0])
by_id = {int(o.split(" ·")[0]): o for o in opts}
assert len(by_id) == len(rfm) == 4318
assert 12346 not in by_id and 16446 not in by_id   # fully/mostly-cancelled customers correctly excluded
seen = set()
sample = list(rfm.groupby("Segment", observed=True).head(3)["CustomerID"]) + [17850, 14646, 18102, 12347]
for cid in sample:
    at.selectbox[0].set_value(by_id[int(cid)]).run()
    assert not at.exception, (cid, errs(at))
    hero = [m.value for m in at.markdown if (chr(60) + "div class=\"seg-hero\"") in m.value]
    seg = rfm.loc[rfm.CustomerID == cid, "Segment"].iat[0]
    assert hero and f"Customer {cid}" in hero[0] and str(seg) in hero[0], (cid, seg)
    seen.add(str(seg))
print("  customers tested:", len(sample), "| segments covered:", len(seen), sorted(seen))
assert len(seen) == 9
# segment filter
at.multiselect[0].set_value(["At Risk"]).run(); assert not at.exception, errs(at)
at.button[0].click().run(); assert not at.exception, errs(at)
print("  segment filter + random button OK")
print("ALL TESTS PASSED")
