"""Cut product stills / parts out of the website recording (rembg isnet) + logo/wordmark masks."""
import json
import sys

import numpy as np
from PIL import Image, ImageFilter
from rembg import new_session, remove

FR, CL, OUT = sys.argv[1], sys.argv[2], sys.argv[3]  # frames dir, clips dir, output assets dir
sess = new_session("isnet-general-use")


def tight(im, pad=4):
    a = np.asarray(im)[..., 3]
    ys, xs = np.where(a > 10)
    return im.crop((max(0, xs.min() - pad), max(0, ys.min() - pad), xs.max() + pad + 1, ys.max() + pad + 1))


def cut(im, name, post=None):
    out = remove(im.convert("RGB"), session=sess, post_process_mask=True)
    if post:
        out = post(out)
    out = tight(out)
    out.save(f"{OUT}/{name}.png")
    print(name, out.size)
    return out


def mask_white(im, lo=110, hi=200, scale=6, blur=1.6):
    """White logo on dark bg -> crisp white RGBA (upscaled, re-thresholded)."""
    L = im.convert("L").resize((im.width * scale, im.height * scale), Image.BICUBIC).filter(ImageFilter.GaussianBlur(blur))
    a = np.clip((np.asarray(L, np.float32) - lo) / (hi - lo), 0, 1)
    a = a * a * (3 - 2 * a)
    o = np.zeros(a.shape + (4,), np.uint8)
    o[..., :3] = 255
    o[..., 3] = (a * 255).astype(np.uint8)
    return tight(Image.fromarray(o, "RGBA"), 2)


f1 = Image.open(f"{FR}/t1.0.png").convert("RGB")
mask_white(f1.crop((28, 12, 192, 78))).save(f"{OUT}/logo.png")
f142 = Image.open(f"{FR}/t14.2.png").convert("RGB")
mask_white(f142.crop((955, 405, 1785, 500)), 120, 210, 3, 1.0).save(f"{OUT}/havoc.png")
# brand red from the Play Sound button
# brand red, sampled from the "Play Sound" button on the hero section of the page: (188, 0, 46)
json.dump({"red": [188, 0, 46]}, open(f"{OUT}/brand.json", "w"))

cut(Image.open(f"{CL}/rgb/069.jpg"), "kb_rgb")
cut(Image.open(f"{CL}/rgb/001.jpg"), "kb_dark")
cut(Image.open(f"{FR}/t13.4.png").crop((480, 100, 1420, 820)), "kb_tilt")
cut(Image.open(f"{FR}/t8.6.png").crop((440, 290, 1460, 665)), "kb_gasket")
cut(Image.open(f"{FR}/t22.8.png").crop((150, 520, 830, 830)), "keycap")
cut(Image.open(f"{CL}/hotswap/001.jpg"), "kb_swap")
f1b = Image.open(f"{FR}/t1.0.png").convert("RGB").crop((86, 340, 1000, 880))
cut(f1b, "kb_hero")

# switch parts (each from the frame where it is fully in view)
vt = Image.open(f"{CL}/venom/013.jpg")
vm = Image.open(f"{CL}/venom/026.jpg")
vb = Image.open(f"{CL}/venom/038.jpg")
for nm, im in [("v_top_src", vt), ("v_mid_src", vm), ("v_base_src", vb)]:
    im.save(f"{OUT}/{nm}.jpg")
cut(vm.crop((190, 195, 350, 460)), "sw_stem")
cut(vm.crop((236, 485, 312, 690)), "sw_spring")
print("ok")
