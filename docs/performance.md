# Performance and Resource Limits

## Design constraints

The library is designed for receipt-scale output on a single serial connection. It is not optimized for throughput; correctness and predictability are the priorities.

---

## Memory model

Images are never held in memory as complete 1-bit arrays before transmission. The pipeline processes and sends one band at a time:

```
full image (any size)
  → Pillow resize (intermediate, GC'd after conversion)
  → 1-bit image (full, in RAM briefly)
  → BitPacker → MonoRaster (full, in RAM)
  → sliced into bands of config.image_chunk_height rows
  → each band encoded and written to transport immediately
  → band discarded before next band is packed
```

The maximum memory held at one time is approximately:

```
peak ≈ original_image_bytes + (dots_per_line × image_height × 1 bit)
     + (dots_per_line × image_chunk_height × 1 bit)  ← active band
```

For a full-width 384-dot image at 200 rows: `≈ 384 × 200 / 8 = 9 600 bytes` — negligible.

### Tuning

`config.image_chunk_height` (default 24) controls band height. Lower values reduce peak memory at the cost of more transport round-trips per image. Raise it if the printer's internal buffer can absorb larger bands; lower it if you observe buffer-overrun artifacts.

---

## Expected throughput

Actual throughput depends on the serial baud rate and printer internal buffer. Rough estimates at 115200 baud:

| Operation | Approximate data | Expected time |
|-----------|-----------------|---------------|
| `initialize()` | 2 bytes | < 1 ms |
| `text("Hello\n")` native | 6 bytes | < 1 ms |
| `feed(3)` | 3 bytes | < 1 ms |
| 384 × 100px image | ~5 KB | ~0.5 s |
| 384 × 500px image | ~25 KB | ~2 s |
| Raster text line (384px wide) | ~1–2 KB | ~0.1 s |

These are byte-transmission estimates only. Actual wall-clock time includes printer mechanical speed, which is the dominant factor at receipt scale.

**Baseline measurements against the physical hardware should be taken once the printer arrives and documented here.** The values above are order-of-magnitude guides only.

---

## Text rasterization

Rasterizing a single text line with Pillow requires:

1. Font lookup (cached after first resolve)
2. One `textbbox` measurement call
3. One `Image.new` + `ImageDraw.text` + `convert("1")` sequence

For typical receipt lines (< 50 characters, 24pt font), this is fast enough to be imperceptible. For documents with many raster-fallback lines (e.g. pages of Greek text), rasterization time may accumulate. Profile with `cProfile` if this becomes a bottleneck.

---

## SVG rendering

`VectorRenderer` calls CairoSVG synchronously. CairoSVG performance depends on:

- SVG complexity (paths, filters, gradients)
- Output resolution (`output_width` passed to `cairosvg.svg2png`)
- libcairo version on the system

For a simple logo SVG, expect < 1 second. For complex diagrams, allow several seconds. There is no timeout or cancellation mechanism in v0.1; add one at the call site if needed.

---

## Serial transport

`SerialTransport` calls `serial.Serial.write()` directly. `pyserial` buffers writes in the OS serial driver. If the printer's internal buffer overflows (visible as garbled or missing output), reduce `image_chunk_height` to send smaller commands, or add a `time.sleep()` between bands at the call site.

No flow control or hardware handshaking is enabled by default. If the printer supports RTS/CTS, configure it in `SerialTransport` and document the result in [docs/hardware.md](hardware.md).
