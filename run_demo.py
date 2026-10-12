import time
from src.metrica_parser import MetricaTrackingParser
from src.pipeline import FullPossessionPipeline
from src.visualizer import PitchVisualizer

def main():
    print("=" * 65)
    print("⚽ RUNNING FOOTBALL POSSESSION TRACKER END-TO-END DEMO")
    print("=" * 65)

    parser = MetricaTrackingParser()
    pipeline = FullPossessionPipeline()
    visualizer = PitchVisualizer()

    # 1. Load match tracking dataset
    dataset_path = "data/sample_match_tracking.json"
    print(f"\n[1] Ingesting match tracking dataset from: {dataset_path}")
    frames = parser.load_json_match(dataset_path)
    print(f"    --> Successfully parsed {len(frames)} tracking frames (25 FPS).")

    # 2. Process frames through pipeline
    print("\n[2] Executing FullPossessionPipeline (Kinematics + Pitch Control + Markov)...")
    start_time = time.time()
    
    home_frames = 0
    away_frames = 0
    contested_frames = 0
    turnovers = []
    last_team = None

    for i, frame in enumerate(frames):
        res = pipeline.process_frame(frame)
        team = res["smoothed_team"]
        
        if team == "Home":
            home_frames += 1
        elif team == "Away":
            away_frames += 1
        else:
            contested_frames += 1

        if last_team and team and team != last_team and team != "Contested":
            turnovers.append((frame["frame_id"], last_team, team))
        if team != "Contested":
            last_team = team

    elapsed_ms = (time.time() - start_time) * 1000
    avg_fps = len(frames) / (elapsed_ms / 1000)

    print(f"    --> Processed {len(frames)} frames in {elapsed_ms:.1f} ms ({avg_fps:.1f} FPS / {elapsed_ms/len(frames):.2f} ms per frame).")

    # 3. Print match metrics
    total = len(frames)
    print("\n[3] Match Analytics Summary:")
    print(f"    • Home Possession      : {home_frames / total * 100:.1f}% ({home_frames} frames)")
    print(f"    • Away Possession      : {away_frames / total * 100:.1f}% ({away_frames} frames)")
    print(f"    • Contested / Loose Ball: {contested_frames / total * 100:.1f}% ({contested_frames} frames)")
    print(f"    • Detected Turnovers   : {len(turnovers)}")
    for fid, t_from, t_to in turnovers:
        print(f"       -> Frame #{fid:03d}: Turnover from {t_from} to {t_to}")

    # 4. Render sample key frames
    print("\n[4] Rendering visual tactical diagrams with Pitch Control Heatmap...")
    for fid in [25, 52, 90]:
        sample_f = frames[fid - 1]
        pc_surface = pipeline.pitch_control_engine.calculate_pitch_control_surface(
            [p for p in sample_f['players'] if p['team'] == 'Home'],
            [p for p in sample_f['players'] if p['team'] == 'Away']
        )['home_surface']
        
        out_img = f"data/demo_frame_{fid}.png"
        visualizer.render_frame(sample_f, pc_surface, out_img, title=f"Match Possession - Frame #{fid}")
        print(f"    • Rendered: {out_img}")

    print("\n" + "=" * 65)
    print("✅ DEMO EXECUTION COMPLETE! All components working smoothly.")
    print("=" * 65)

if __name__ == "__main__":
    main()
