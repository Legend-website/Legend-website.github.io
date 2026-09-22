#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
VIDEOS = ROOT / "static" / "videos"
IMAGES = ROOT / "static" / "images" / "paper"
PLATFORMS = ROOT / "static" / "images" / "platforms"
OUT = VIDEOS / "legend_overview.mp4"
TMP = ROOT / "tools" / ".overview_tmp"
FONT = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"

W, H = 1920, 1080
FPS = 30
HEADER_H = 96
CAPTION_H = 96
GRID_Y = HEADER_H
CELL_W = W // 2
CELL_H = (H - HEADER_H - CAPTION_H) // 2
PAD_COLOR = "0x070810"

C_PRIMARY = (0, 100, 150)
C_DEEP = (15, 77, 112)
C_EMERALD = (13, 143, 122)
C_BG = (7, 16, 24)
C_WHITE = (255, 255, 255)
OVERLAY_BG = (8, 22, 34, 88)
OVERLAY_BG_STRONG = (8, 22, 34, 108)
FADE_IN = 0.85
FADE_OUT = 0.55


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def ffprobe_duration(path: Path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        text=True,
    )
    return float(json.loads(out)["format"]["duration"])


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if draw.textlength(test, font=font) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def rounded_rect(draw: ImageDraw.ImageDraw, box: tuple, radius: int, fill: tuple) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def gradient_bg(top=(10, 24, 36), bottom=C_BG) -> Image.Image:
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        for x in range(W):
            px[x, y] = c
    return img


def save_card(path: Path, section: str | None, title: str, body: str | None = None, bullets: list[str] | None = None) -> None:
    img = gradient_bg()
    draw = ImageDraw.Draw(img)
    y = 130 if section else 180
    if section:
        sf = load_font(42, True)
        sw = draw.textlength(section, font=sf)
        draw.text(((W - sw) / 2, y), section, fill=C_PRIMARY, font=sf)
        y += 64
        draw.rectangle([(W - 220) // 2, y, (W + 220) // 2, y + 4], fill=C_PRIMARY)
        y += 40
    tf = load_font(72, True)
    for line in wrap(draw, title, tf, W - 200):
        tw = draw.textlength(line, font=tf)
        draw.text(((W - tw) / 2, y), line, fill=C_WHITE, font=tf)
        y += 82
    if body:
        bf = load_font(42)
        y += 22
        for line in wrap(draw, body, bf, W - 240):
            tw = draw.textlength(line, font=bf)
            draw.text(((W - tw) / 2, y), line, fill=(220, 232, 240), font=bf)
            y += 54
    if bullets:
        y += 28
        bf = load_font(38)
        for b in bullets:
            for line in wrap(draw, f"•  {b}", bf, W - 260):
                draw.text((150, y), line, fill=(210, 228, 238), font=bf)
                y += 50
    img.save(path)


def save_title(path: Path) -> None:
    img = gradient_bg((8, 20, 32), (4, 12, 20))
    draw = ImageDraw.Draw(img)
    lf = load_font(118, True)
    legend = "LEGEND"
    lw = draw.textlength(legend, font=lf)
    draw.text(((W - lw) / 2, 300), legend, fill=(120, 200, 245), font=lf)
    sf = load_font(40)
    y = 460
    for line in [
        "Leg-enhanced Degeneracy-aware State Estimation",
        "in Challenging Scenarios for Legged Robots",
    ]:
        tw = draw.textlength(line, font=sf)
        draw.text(((W - tw) / 2, y), line, fill=(230, 240, 246), font=sf)
        y += 52
    tf = load_font(34)
    tag = "Degeneracy-Aware Fusion for Legged Odometry"
    tw = draw.textlength(tag, font=tf)
    draw.text(((W - tw) / 2, 610), tag, fill=C_EMERALD, font=tf)
    draw.rectangle([(W - 280) // 2, 690, (W + 280) // 2, 694], fill=C_PRIMARY)
    img.save(path)


def save_dual_platform_base(
    path: Path,
    left: Path,
    right: Path,
    left_label: str,
    right_label: str,
) -> None:
    img = gradient_bg()
    draw = ImageDraw.Draw(img)
    y0, y1 = 88, H - CAPTION_H - 52
    gap = 40
    half_w = (W - gap * 3) // 2
    for col, (im_path, label) in enumerate([(left, left_label), (right, right_label)]):
        x0 = gap + col * (half_w + gap)
        rounded_rect(draw, (x0, y0, x0 + half_w, y1), 14, (245, 248, 252))
        im = Image.open(im_path).convert("RGB")
        iw, ih = im.size
        inner_h = y1 - y0 - 58
        scale = min((half_w - 48) / iw, inner_h / ih)
        nw, nh = int(iw * scale), int(ih * scale)
        im = im.resize((nw, nh), Image.Resampling.LANCZOS)
        px = x0 + (half_w - nw) // 2
        py = y0 + 18 + (inner_h - nh) // 2
        img.paste(im, (px, py))
        lf = load_font(30, True)
        lw = draw.textlength(label, font=lf)
        draw.text((x0 + (half_w - lw) / 2, y1 - 44), label, fill=C_PRIMARY, font=lf)
    img.save(path)


def save_image_base(path: Path, image: Path) -> None:
    base = gradient_bg()
    im = Image.open(image).convert("RGB")
    iw, ih = im.size
    scale = min((W - 120) / iw, (H - CAPTION_H - 80) / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    base.paste(im, ((W - nw) // 2, (H - CAPTION_H - nh) // 2 + 20))
    base.save(path)


def save_header_overlay(path: Path, section: str, subtitle: str = "") -> None:
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    rounded_rect(draw, (40, 28, min(W - 40, 920), 88), 12, OVERLAY_BG_STRONG)
    draw.text((64, 40), section, fill=(*C_PRIMARY, 255), font=load_font(32, True))
    if subtitle:
        draw.text((64, 72), subtitle, fill=(220, 235, 245, 230), font=load_font(24))
    overlay.save(path)


def save_caption_overlay(path: Path, label: str, caption: str, metric: str = "") -> None:
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    y0 = H - CAPTION_H - 16
    rounded_rect(draw, (40, y0, W - 40, H - 16), 12, OVERLAY_BG)
    draw.rectangle([40, y0, 48, H - 16], fill=(*C_PRIMARY, 200))
    draw.text((64, y0 + 14), label, fill=(150, 210, 240, 255), font=load_font(28, True))
    draw.text((64, y0 + 46), caption, fill=(245, 250, 252, 245), font=load_font(24))
    if metric:
        mw = draw.textlength(metric, font=load_font(22, True))
        draw.text((W - 64 - mw, y0 + 46), metric, fill=(120, 220, 200, 255), font=load_font(22, True))
    overlay.save(path)


def save_grid_overlay(path: Path, section: str, subtitle: str, label: str, caption: str, metric: str = "") -> None:
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    rounded_rect(draw, (40, 20, min(W - 40, 980), 86), 12, OVERLAY_BG_STRONG)
    draw.text((64, 32), section, fill=(*C_PRIMARY, 255), font=load_font(30, True))
    if subtitle:
        draw.text((64, 62), subtitle, fill=(215, 230, 240, 225), font=load_font(22))
    y0 = H - CAPTION_H - 12
    rounded_rect(draw, (40, y0, W - 40, H - 12), 12, OVERLAY_BG)
    draw.rectangle([40, y0, 48, H - 12], fill=(*C_PRIMARY, 200))
    draw.text((64, y0 + 12), label, fill=(150, 210, 240, 255), font=load_font(26, True))
    draw.text((64, y0 + 42), caption, fill=(245, 250, 252, 245), font=load_font(22))
    if metric:
        mw = draw.textlength(metric, font=load_font(21, True))
        draw.text((W - 64 - mw, y0 + 42), metric, fill=(120, 220, 200, 255), font=load_font(21, True))
    overlay.save(path)


def save_grid_cell_labels(path: Path, labels: list[str]) -> None:
    gw, gh = CELL_W * 2, CELL_H * 2
    overlay = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = load_font(26, True)
    positions = [(0, 0), (CELL_W, 0), (0, CELL_H), (CELL_W, CELL_H)]
    for (cx, cy), text in zip(positions, labels):
        lines = wrap(draw, text, font, CELL_W - 36)
        line_h = 34
        pad_x, pad_y = 14, 10
        text_w = max((draw.textlength(line, font=font) for line in lines), default=0)
        box_w = int(text_w + pad_x * 2 + 6)
        box_h = len(lines) * line_h + pad_y * 2
        box = (cx + 12, cy + 12, cx + 12 + box_w, cy + 12 + box_h)
        rounded_rect(draw, box, 8, (8, 22, 34, 168))
        draw.rectangle([box[0], box[1], box[0] + 5, box[3]], fill=(*C_PRIMARY, 215))
        y = cy + 12 + pad_y
        for line in lines:
            draw.text((cx + 12 + pad_x + 4, y), line, fill=(245, 250, 252, 252), font=font)
            y += line_h
    overlay.save(path)


def fade_filter(duration: float) -> str:
    fin = min(FADE_IN, duration * 0.28)
    fout = min(FADE_OUT, duration * 0.22)
    start = max(duration - fout, 0)
    return f"fade=t=in:st=0:d={fin:.3f},fade=t=out:st={start:.3f}:d={fout:.3f}"


def fit_cell_filter(idx: int, seg_dur: float, src_dur: float, realtime: bool = False) -> str:
    if realtime:
        speed = 1.0
    else:
        speed = max(src_dur / seg_dur, 1.0) if seg_dur > 0 else 1.0
    return (
        f"[{idx}:v]setpts=PTS/{speed:.4f},"
        f"scale={CELL_W}:{CELL_H}:force_original_aspect_ratio=decrease,"
        f"pad={CELL_W}:{CELL_H}:(ow-iw)/2:(oh-ih)/2:color={PAD_COLOR},"
        f"fps={FPS},trim=duration={seg_dur},setpts=PTS-STARTPTS[v{idx}]"
    )


def png_to_video(png: Path, duration: float, out: Path, overlay: Path | None = None) -> None:
    fade = fade_filter(duration)
    if overlay:
        run([
            "ffmpeg", "-y", "-loop", "1", "-i", str(png), "-i", str(overlay),
            "-t", f"{duration}",
            "-filter_complex",
            f"[0:v]scale={W}:{H}[bg];[1:v]format=rgba[ov];[bg][ov]overlay=0:0,{fade}[v]",
            "-map", "[v]", "-r", str(FPS),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "20", str(out),
        ])
    else:
        run([
            "ffmpeg", "-y", "-loop", "1", "-i", str(png),
            "-t", f"{duration}", "-vf", f"scale={W}:{H},{fade}", "-r", str(FPS),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "20", str(out),
        ])


def make_grid_segment(
    out: Path,
    clips: list[Path],
    duration: float,
    overlays: list[tuple[str, str, str]],
    section: str,
    subtitle: str,
    cycle_captions: bool = True,
    realtime_cells: set[int] | None = None,
    cell_labels: list[str] | None = None,
) -> None:
    base = TMP / f"{out.stem}_base.mp4"
    rt = realtime_cells or set()
    labels = cell_labels or [""] * len(clips)
    label_png = TMP / f"{out.stem}_cell_labels.png"
    save_grid_cell_labels(label_png, labels)
    durs = [ffprobe_duration(p) for p in clips]
    label_in = len(clips)
    parts = [fit_cell_filter(i, duration, d, realtime=(i in rt)) for i, d in enumerate(durs)]
    parts += [
        "[v0][v1]hstack=inputs=2[top]",
        "[v2][v3]hstack=inputs=2[bot]",
        "[top][bot]vstack=inputs=2[grid]",
        f"[{label_in}:v]format=rgba[celllabels]",
        "[grid][celllabels]overlay=0:0[gridl]",
        f"color=c={PAD_COLOR}:s={W}x{H}:d={duration}:r={FPS}[bg]",
        f"[bg][gridl]overlay=0:{GRID_Y}[vout]",
    ]
    cmd = ["ffmpeg", "-y"]
    for p in clips:
        cmd += ["-stream_loop", "-1", "-i", str(p)]
    cmd += ["-i", str(label_png)]
    cmd += [
        "-filter_complex", ";".join(parts),
        "-map", "[vout]", "-t", f"{duration}", "-an",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "20",
        str(base),
    ]
    run(cmd)

    if not cycle_captions:
        label, cap, metric = overlays[0]
        ov = TMP / f"ov_{out.stem}_static.png"
        save_grid_overlay(ov, section, subtitle, label, cap, metric)
        run([
            "ffmpeg", "-y", "-i", str(base), "-i", str(ov),
            "-filter_complex",
            f"[0:v]copy[base];[1:v]format=rgba[ov];[base][ov]overlay=0:0,{fade_filter(duration)}[v]",
            "-map", "[v]", "-an",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "20",
            str(out),
        ])
        return

    step = duration / len(overlays)
    chunk_paths: list[Path] = []
    for i, (label, cap, metric) in enumerate(overlays):
        ov = TMP / f"ov_{out.stem}_{i}.png"
        save_grid_overlay(ov, section, subtitle, label, cap, metric)
        chunk = TMP / f"{out.stem}_p{i}.mp4"
        run([
            "ffmpeg", "-y", "-ss", f"{i * step:.3f}", "-i", str(base), "-i", str(ov),
            "-t", f"{step:.3f}",
            "-filter_complex",
            f"[0:v]setpts=PTS-STARTPTS[base];[1:v]format=rgba[ov];[base][ov]overlay=0:0[v]",
            "-map", "[v]", "-an",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "20",
            str(chunk),
        ])
        chunk_paths.append(chunk)

    lst = TMP / f"{out.stem}_parts.txt"
    lst.write_text("\n".join(f"file '{p}'" for p in chunk_paths))
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "20",
        str(out),
    ])


def concat_segments(segments: list[Path], out: Path) -> None:
    lst = TMP / "concat.txt"
    lst.write_text("\n".join(f"file '{p}'" for p in segments))
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "20",
        str(out),
    ])


def build() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()

    cards = {
        "title": (save_title, None),
        "motivation": (save_card, ("Motivation", "Legged SLAM fails when foot slip meets sensor degeneracy",
                                    "Existing systems apply kinematic constraints on every contact and treat LiDAR and visual degradation separately.", None)),
        "sals": (save_card, ("Contribution I", "Slip-Aware Leg Scheduling (SALS)", None, [
            "Per-foot slip score, IMU consistency, and geometry weights gate leg factors",
            "LiDAR / visual degeneracy detection activates or suppresses exteroceptive updates",
            "Single filter–optimizer stack for quadrupeds and bipeds",
        ])),
        "eval": (save_card, ("Evaluation", "Three-tier benchmark protocol", None, [
            "Q1 · GrandTour — public quadruped LVIO accuracy",
            "Q2 · GLIDE — robustness under slip and degeneracy",
            "Q3 · KILVO / LIKO — cross-platform biped and humanoid validation",
        ])),
        "closing": (save_card, (None, "LEGEND · GLIDE · Comprehensive Evaluation",
                                "Degeneracy-aware legged LVIO with reliability-aware fusion for quadrupeds and bipeds.",
                                ["Code and GLIDE dataset to be released upon acceptance"])),
    }

    pngs: dict[str, Path] = {}
    for name, (fn, args) in cards.items():
        p = TMP / f"{name}.png"
        if args is None:
            fn(p)
        else:
            fn(p, *args)
        pngs[name] = p

    image_scenes: dict[str, tuple[str, str, str]] = {
        "pipeline": ("LEGEND Framework",
                     "IESKF frontend fuses IMU, LiDAR, vision, and leg factors at LiDAR rate.",
                     "SALS reweights or rejects unreliable leg contacts."),
        "glide": ("GLIDE Benchmark",
                  "32 real-robot + 10 simulation sequences with synchronized multi-modal streams.",
                  "Covers slip, soft terrain, and sensor degeneracy."),
        "teaser": ("Qualitative Results",
                   "SALS prevents drift during foot slip under active contact.",
                   "LEGEND preserves sharper map geometry than fixed-weight leg fusion."),
        "platforms": ("Q3 · Cross-Platform Validation",
                      "LIKO (BHR-B3) and KILVO (Unitree G1) humanoid platforms share the same proprioceptive interface.",
                      "Quadruped and biped support without changing the state formulation."),
    }
    image_pngs: dict[str, Path] = {}
    image_overlays: dict[str, Path] = {}
    image_files = {
        "pipeline": IMAGES / "legend_pipeline.png",
        "glide": IMAGES / "a2.png",
        "teaser": IMAGES / "legend_teaser.png",
    }
    for name, (section, cap, metric) in image_scenes.items():
        image_pngs[name] = TMP / f"{name}_base.png"
        image_overlays[name] = TMP / f"{name}_cap.png"
        if name == "platforms":
            save_dual_platform_base(
                image_pngs[name],
                PLATFORMS / "liko_bhr_b3.png",
                PLATFORMS / "kilvo_g1.png",
                "LIKO · BHR-B3",
                "KILVO · Unitree G1",
            )
        else:
            save_image_base(image_pngs[name], image_files[name])
        save_caption_overlay(image_overlays[name], section, cap, metric)

    segs: list[tuple[str, float]] = [
        ("title", 5.0),
        ("motivation", 5.0),
        ("challenge", 8.0),
        ("pipeline", 9.0),
        ("sals", 6.0),
        ("glide", 5.0),
        ("eval", 4.0),
        ("grandtour", 14.0),
        ("glide_res", 14.0),
        ("platforms", 5.0),
        ("cross", 10.0),
        ("teaser", 5.0),
        ("closing", 4.0),
    ]

    seg_paths: list[Path] = []
    for name, dur in segs:
        out = TMP / f"seg_{name}.mp4"
        if name == "challenge":
            make_grid_segment(
                out,
                [VIDEOS / "glide_corridor.mp4", VIDEOS / "glide_foot_kick.mp4",
                 VIDEOS / "glide_dark_stop.mp4", VIDEOS / "glide_grass_slope.mp4"],
                dur,
                [
                    ("Challenging Scenarios", "Corridor · Foot-kick · Low-light · Soft terrain", "Slip + degeneracy"),
                ],
                "Challenging Scenarios",
                "Coupled proprioceptive slip and exteroceptive degeneracy",
                cycle_captions=False,
                realtime_cells={1},
                cell_labels=["Corridor", "Foot-kick slip", "Low-light", "Soft terrain"],
            )
        elif name == "grandtour":
            make_grid_segment(
                out,
                [VIDEOS / "snow.mp4", VIDEOS / "eig.mp4", VIDEOS / "arc.mp4", VIDEOS / "spx.mp4"],
                dur,
                [
                    ("Q1 · GrandTour", "SNOW-2 · EIG-1 · ARC-2 · SPX-2", "Lowest RTE on 3/4 sequences"),
                ],
                "Q1 · GrandTour",
                "Lowest RTE on 3/4 sequences; competitive on Arc-2",
                cycle_captions=False,
                cell_labels=["SNOW-2", "EIG-1", "ARC-2", "SPX-2"],
            )
        elif name == "glide_res":
            make_grid_segment(
                out,
                [VIDEOS / "kick.mp4", VIDEOS / "parking.mp4", VIDEOS / "slip.mp4", VIDEOS / "sandstone.mp4"],
                dur,
                [
                    ("Q2 · GLIDE", "KICK · SLIP · PARKINGLOT · SANDSTONE", "Cutting-edge performance"),
                ],
                "Q2 · GLIDE",
                "Robustness under slip and degradation",
                cycle_captions=False,
                cell_labels=["KICK", "SLIP", "PARKINGLOT", "SANDSTONE"],
            )
        elif name == "cross":
            make_grid_segment(
                out,
                [VIDEOS / "LIKO_square_walk.mp4", VIDEOS / "LIKO_up_slope.mp4", VIDEOS / "h1.mp4", VIDEOS / "b2.mp4"],
                dur,
                [
                    ("Q3 · Cross-Platform", "LIKO biped · KILVO humanoid", "LEGEND (KLIO) · LEGEND (Full)"),
                ],
                "Q3 · Cross-Platform",
                "LEGEND (KLIO) lowest on LIKO; LEGEND (Full) stable on KILVO",
                cycle_captions=False,
                cell_labels=["LIKO · Square Walk", "LIKO · Up Slope", "KILVO · H1", "KILVO · B2"],
            )
        elif name in image_pngs:
            png_to_video(image_pngs[name], dur, out, overlay=image_overlays[name])
        else:
            png_to_video(pngs[name], dur, out)
        seg_paths.append(out)
        print(f"done {name} ({dur}s)")

    concat_segments(seg_paths, OUT)
    total = sum(d for _, d in segs)
    print(f"Wrote {OUT} · {total:.0f}s · {OUT.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    build()
