#!/usr/bin/env python3
"""Record the runway monitor headless (Playwright Chromium) → MP4 / PNG.

  python3 viz/live_server.py &                                   # serves viz/ + live parser on :8090
  python3 viz/record.py clip  "mode=asis&variant=unresolved&freeze=98" docs/video/sfo_28l_asis_2x.mp4
  python3 viz/record.py clip  "mode=gmaps&variant=resolved"           docs/video/sfo_28l_gmaps_2x.mp4
  python3 viz/record.py still "mode=asis&variant=unresolved&freeze=98" docs/runway_monitor_sfo_28l_asis.png --at 98 --size 1920x1200

Clips: 1440×900, recorded at page speed 1× and sped up --speedup (default 2×) with ffmpeg setpts, so live-parser results land
in the panel exactly where they arrived; 25 fps H.264, no audio, live panel on (?live=1) unless --no-live.
The page sets window.__done at the end of the scenario (or 4 s after the as-is freeze); recording stops there.
Needs: pip install playwright imageio-ffmpeg && playwright install chromium (ffmpeg comes from imageio-ffmpeg if not on PATH).
"""
import argparse, os, shutil, subprocess, sys, tempfile, time

from playwright.sync_api import sync_playwright


def ffmpeg_exe():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["clip", "still"])
    ap.add_argument("query")
    ap.add_argument("out")
    ap.add_argument("--base", default="http://localhost:8090/")
    ap.add_argument("--size", default="1440x900")
    ap.add_argument("--at", type=float, help="still: scenario time to capture (page plays at 8x to get there)")
    ap.add_argument("--no-live", action="store_true")
    ap.add_argument("--settle-s", type=float, default=2.5, help="still: wait this long after stopping (lets the last live-parser result land)")
    ap.add_argument("--max-s", type=float, default=400)
    ap.add_argument("--speedup", type=float, default=2.0, help="clip: record the page at 1x, then speed the video up this much in ffmpeg (setpts) so live results land where they happened")
    ap.add_argument("--card-s", type=float, default=3.0, help="title/closing card length in the FINAL video")
    a = ap.parse_args()
    w, h = map(int, a.size.split("x"))
    q = a.query + ("" if a.no_live else "&live=1")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        if a.kind == "still":
            page = browser.new_page(viewport={"width": w, "height": h})
            page.goto(f"{a.base}?{q}&speed=2", wait_until="networkidle")
            page.wait_for_function("() => window.scn !== undefined || document.querySelector('#statebody')", timeout=30000)
            page.wait_for_timeout(1500)
            page.evaluate("() => document.getElementById('play').click()")
            # play in real time at 2x so the live calls land in the panel like in the clip
            # stop either where the page freezes itself (scenario freeze time) or just past --at
            page.wait_for_function(f"() => window.__frozen === true || parseFloat(document.getElementById('clock').textContent.split('=')[1]) >= {a.at + 0.02}", timeout=int(a.max_s * 1000), polling=50)
            if not page.evaluate("() => window.__frozen === true") and "freeze" not in q:
                page.evaluate("() => document.getElementById('play').click()")
            page.wait_for_timeout(int(a.settle_s * 1000))  # last live call + caption settle
            page.screenshot(path=a.out)
            print("wrote", a.out)
            browser.close()
            return
        tmp = tempfile.mkdtemp()
        ctx = browser.new_context(viewport={"width": w, "height": h}, record_video_dir=tmp, record_video_size={"width": w, "height": h})
        page = ctx.new_page()
        t0 = time.time()
        page.goto(f"{a.base}?{q}&speed=1&autoplay=1&cardms={int(a.card_s * a.speedup * 1000)}", wait_until="domcontentloaded")
        page.wait_for_function("() => window.__done === true", timeout=int(a.max_s * 1000), polling=250)
        lead = max(0.0, page.evaluate("() => window.__startedAt || 0") / 1000 - 0.2)  # trim the page-load lead-in (card starts at __startedAt)
        live = page.evaluate("() => window.__live")
        video = page.video.path()
        ctx.close(); browser.close()
        print(f"recorded {time.time() - t0:.1f} s (trim {lead:.1f} s); live calls: {len(live)}; latencies ms: {[round(c['latency_ms']) for c in live]}")
        # Playwright's webm is variable frame rate; re-time to constant 25 fps H.264.
        subprocess.run([ffmpeg_exe(), "-y", "-loglevel", "error", "-ss", f"{lead}", "-i", video, "-vf", f"setpts=PTS/{a.speedup},scale={w}:{h}", "-r", "25", "-an",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart", a.out], check=True)
        print("wrote", a.out)


if __name__ == "__main__":
    sys.exit(main())
