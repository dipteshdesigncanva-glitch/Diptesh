import sys, time
from rembg import remove, new_session
from PIL import Image
model=sys.argv[1]; s=new_session(model)
for f in sys.argv[2:]:
    t=time.time(); im=Image.open(f).convert('RGB')
    out=remove(im, session=s, post_process_mask=False)
    out.save(f.rsplit('.',1)[0]+f'_{model}.png'); print(f, model, round(time.time()-t,1),'s', flush=True)
