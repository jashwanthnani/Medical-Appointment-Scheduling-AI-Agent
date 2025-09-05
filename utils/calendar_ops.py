# utils/calendar_ops.py
import pandas as pd

SHEET = "Schedule"

def load_schedule(path="doctors.xlsx"):
    return pd.read_excel(path, sheet_name=SHEET)

def save_schedule(df: pd.DataFrame, path="doctors.xlsx"):
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name=SHEET)

def to_minutes(tstr: str) -> int:
    hh, mm = map(int, tstr.split(":"))
    return hh * 60 + mm

def minutes_to_str(m: int) -> str:
    return f"{m//60:02d}:{m%60:02d}"

def get_doctors(df: pd.DataFrame):
    return sorted(df["Doctor"].dropna().unique().tolist())

def get_locations(df: pd.DataFrame, doctor: str):
    return sorted(df[df["Doctor"] == doctor]["Location"].dropna().unique().tolist())

def get_dates(df: pd.DataFrame, doctor: str, location: str):
    sub = df[(df["Doctor"] == doctor) & (df["Location"] == location)]
    return sorted(sub["Date"].dropna().unique().tolist())

def contiguous_blocks_for_duration(df_day: pd.DataFrame, minutes_required: int):
    slots = df_day.sort_values("Start").reset_index(drop=True)
    needed = max(1, minutes_required // int(slots.iloc[0]["SlotMinutes"])) if not slots.empty else 0
    options = []
    for i in range(len(slots)):
        ok = True
        for k in range(needed):
            j = i + k
            if j >= len(slots) or str(slots.loc[j, "Available"]).lower() != "yes":
                ok = False
                break
            if k > 0:
                prev_end = to_minutes(slots.loc[j-1, "End"])
                curr_start = to_minutes(slots.loc[j, "Start"])
                if curr_start != prev_end:
                    ok = False
                    break
        if ok:
            start = slots.loc[i, "Start"]
            start_min = to_minutes(start)
            end_min = start_min + minutes_required
            options.append((start, minutes_to_str(end_min)))
    return list(dict.fromkeys(options))  # unique

def suggest_slots(df: pd.DataFrame, doctor: str, location: str, date_str: str, minutes_required: int, limit=10):
    day_df = df[(df["Doctor"] == doctor) & (df["Location"] == location) & (df["Date"] == date_str)]
    blocks = contiguous_blocks_for_duration(day_df, minutes_required)
    return blocks[:limit]

def block_slots(df: pd.DataFrame, doctor: str, location: str, date_str: str, start_str: str, minutes_required: int):
    day_df = df[(df["Doctor"] == doctor) & (df["Location"] == location) & (df["Date"] == date_str)].sort_values("Start")
    slot_minutes = 30
    needed = minutes_required // slot_minutes
    idxs = day_df.index[day_df["Start"] == start_str].tolist()
    if not idxs:
        return df, False
    start_idx = idxs[0]
    rows_to_block = []
    prev_end_min = None
    for k in range(needed):
        idx = start_idx + k
        if idx not in day_df.index or str(day_df.loc[idx, "Available"]).lower() != "yes":
            return df, False
        if k > 0 and prev_end_min != to_minutes(day_df.loc[idx, "Start"]):
            return df, False
        prev_end_min = to_minutes(day_df.loc[idx, "End"])
        rows_to_block.append(idx)
    df.loc[rows_to_block, "Available"] = "No"
    end_time = day_df.loc[start_idx + needed - 1, "End"]
    return df, end_time
