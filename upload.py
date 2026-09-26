"""Optional frontend upload route; native IMAGE sockets work without this route."""
import io
import uuid
import zipfile
from pathlib import Path
from aiohttp import web
from server import PromptServer
import folder_paths
from .engine import EXTS


@PromptServer.instance.routes.post('/hotelshow/upload')
async def upload(request):
    parts=await request.multipart()
    entries=[]
    total=0
    async for part in parts:
        if not part.filename:
            continue
        name=Path(part.filename.replace('\\','/')).name
        ext=Path(name).suffix.lower()
        if ext not in EXTS|{'.zip'}:
            raise web.HTTPBadRequest(text='只接受 ZIP、JPG、PNG、WEBP。')
        data=bytearray()
        while True:
            chunk=await part.read_chunk()
            if not chunk:
                break
            total+=len(chunk)
            if total>29*1024*1024:
                raise web.HTTPRequestEntityTooLarge(max_size=29*1024*1024,actual_size=total)
            data.extend(chunk)
        entries.append((name,bytes(data)))
        if len(entries)>24:
            raise web.HTTPBadRequest(text='最多上传 24 张图片。')
    if not entries:
        raise web.HTTPBadRequest(text='没有文件。')
    if any(Path(n).suffix.lower()=='.zip' for n,_ in entries) and len(entries)!=1:
        raise web.HTTPBadRequest(text='ZIP 请单独上传。')
    target=Path(folder_paths.get_input_directory())/'hotelshow'
    target.mkdir(parents=True,exist_ok=True)
    token=uuid.uuid4().hex
    if len(entries)==1:
        name=token+Path(entries[0][0]).suffix.lower()
        (target/name).write_bytes(entries[0][1])
    else:
        name=token+'.zip'
        with zipfile.ZipFile(target/name,'w',compression=zipfile.ZIP_STORED) as z:
            for i,(original,data) in enumerate(entries):
                z.writestr(f'{i+1:03}_{original}',data)
    return web.json_response({'source':'hotelshow/'+name,'count':len(entries)})
