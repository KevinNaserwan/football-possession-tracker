import os
import sys
import time

sys.path.insert(0, "/home/rchandra/git/football-possession-tracker")
from src.metrica_possession_solver import MetricaPossessionSolver

def main():
    print("=" * 70)
    print("Running Metrica Possession Solver (Spearman + Smart Tagging + Hysteresis)")
    print("=" * 70)

    atd_path = "/home/rchandra/git/more-than-a-hack-2027/data/tactical/BAR-ATH_tactical_atd.txt"
    meta_path = "/home/rchandra/git/more-than-a-hack-2027/data/tactical/BAR-ATH_tactical_atd.xml"
    smart_tagging_path = "/home/rchandra/git/more-than-a-hack-2027/data/tactical/BAR-ATH_tactical_smart_tagging.xml"
    out_csv = "/home/rchandra/git/football-possession-tracker/LM10.csv"
    eval_csv = "/home/rchandra/git/more-than-a-hack-2027/evaluation/results/LM10.csv"

    solver = MetricaPossessionSolver(
        pitch_length=105.3,
        pitch_width=68.0,
        reaction_time=0.5,
        max_sprint_speed=7.5,
        lambda_intercept=4.3,
        hysteresis_frames=12,
        smoothing_window=50,
        min_spell_frames=45,
        kinetic_energy_d_threshold=1.15
    )

    t0 = time.time()
    df_sub = solver.solve(
        atd_path=atd_path,
        meta_path=meta_path,
        smart_tagging_path=smart_tagging_path
    )
    elapsed = time.time() - t0

    df_sub.to_csv(out_csv, index=False)
    df_sub.to_csv("/home/rchandra/git/football-possession-tracker/submission.csv", index=False)
    df_sub.to_csv(eval_csv, index=False)
    print(f"Inference completed in {elapsed:.2f} seconds.")
    print(f"Saved submission to {out_csv} ({len(df_sub)} rows).")

    # Counts
    counts = df_sub["label"].value_counts()
    print("\nPredicted Label Distribution:")
    for lbl, cnt in counts.items():
        print(f"  {lbl}: {cnt:,} ({cnt/len(df_sub)*100:.1f}%)")

if __name__ == "__main__":
    main()
