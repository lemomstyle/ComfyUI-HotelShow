import hashlib
import json
import uuid
from pathlib import Path

import numpy as np
import torch
import folder_paths

from .engine import (read_source, contact_sheets, make_prompt, parse_plan,
                     render, MAX_FILES, Image)


def tensor_image(im):
    return torch.from_numpy(np.asarray(im.convert('RGB'),dtype=np.float32)/255.0).unsqueeze(0)


def resolve_input(source):
    root = Path(folder_paths.get_input_directory()).resolve()
    path = (root / source.strip()).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('source 必须指向 ComfyUI/input 内的图片或 ZIP；不能填写你电脑上的路径。')
    return path


class HotelShowPrepare:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {
            'source': ('STRING', {'default':'', 'tooltip':'上传 ZIP/多图后自动填写；也可填写 input 内相对路径'}),
            'hotel_name': ('STRING', {'default':'请填写酒店名称'}),
            'confirmed_facts': ('STRING', {'multiline':True, 'default':'只填写已确认的信息；没有则留空。'}),
            'style': ('STRING', {'multiline':True,'default':'根据照片自动选择风格，留白充分，中文清晰。'}),
        }, 'optional': {f'image{i}': ('IMAGE',) for i in range(1,13)}}

    RETURN_TYPES = ('HOTEL_PHOTOS','IMAGE','STRING','STRING')
    RETURN_NAMES = ('photos','contact_sheets','planning_prompt','input_report')
    FUNCTION = 'prepare'
    CATEGORY = 'HotelShow'

    @classmethod
    def IS_CHANGED(cls, source='', **kwargs):
        if source.strip():
            p = resolve_input(source)
            return hashlib.sha256(p.read_bytes()).hexdigest()
        return 'linked_images'

    def prepare(self,source,hotel_name,confirmed_facts,style,**kwargs):
        if not hotel_name.strip() or hotel_name.strip() == '请填写酒店名称':
            raise ValueError('请先填写真实酒店名称。')
        if len(hotel_name) > 40 or len(confirmed_facts) > 10000 or len(style) > 2000:
            raise ValueError('酒店名称最多 40 字、已确认资料最多 10000 字、风格偏好最多 2000 字。')
        linked = [kwargs[f'image{i}'] for i in range(1,13) if kwargs.get(f'image{i}') is not None]
        if source.strip() and linked:
            raise ValueError('请在 source 上传与 image 连线之间选一种，避免重复素材。')
        if source.strip():
            photos,warnings = read_source(resolve_input(source))
        else:
            photos,warnings,seen = [],[],set()
            if sum(len(batch) for batch in linked) > MAX_FILES:
                raise ValueError('一次最多 24 张图片。')
            for batch in linked:
                for item in batch:
                    a = np.clip(item.detach().cpu().numpy()*255,0,255).astype(np.uint8)
                    im = Image.fromarray(a[:,:,:3]).convert('RGB')
                    im.thumbnail((2400,2400),Image.Resampling.LANCZOS)
                    digest=hashlib.sha256(str(im.size).encode()+im.tobytes()).hexdigest()
                    if digest in seen:
                        warnings.append('连线输入中有像素完全重复的图片，已去重。')
                        continue
                    seen.add(digest)
                    photos.append({'id':f'P{len(photos)+1:03}','name':f'linked_{len(photos)+1:03}.png','image':im})
        if not photos:
            raise ValueError('请上传 ZIP/多图，或连接至少一个 LoadImage。')
        payload={'photos':photos,'hotel_name':hotel_name.strip(),'warnings':warnings}
        sheets=torch.cat([tensor_image(im) for im in contact_sheets(photos)])
        prompt=make_prompt(photos,hotel_name.strip(),confirmed_facts,style)
        report=json.dumps({'count':len(photos),'warnings':warnings,'ids':[
            {'id':p['id'],'name':p['name']} for p in photos]},ensure_ascii=False,indent=2)
        return payload,sheets,prompt,report


class HotelShowRender:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required':{
            'photos':('HOTEL_PHOTOS',),
            'plan_json':('STRING',{'multiline':True,'forceInput':True}),
            'width':('INT',{'default':1080,'min':640,'max':1600,'step':10}),
            'page_height':('INT',{'default':1440,'min':1000,'max':2200,'step':10}),
            'theme':(['auto','ivory','sage','charcoal'],),
            'photo_fit':(['contain','cover'],),
            'title_font':('STRING',{'default':'','tooltip':'留空自动选中文字体；可填写服务端字体路径'}),
            'body_font':('STRING',{'default':''}),
            'manual_plan':('STRING',{'default':'','multiline':True,'tooltip':'可粘贴修订后的完整 JSON；非空时覆盖模型输出'}),
        }}

    RETURN_TYPES=('IMAGE','IMAGE','STRING','STRING')
    RETURN_NAMES=('pages','long_image','layout_report','validated_plan')
    FUNCTION='compose'
    CATEGORY='HotelShow'
    OUTPUT_NODE=True

    def compose(self,photos,plan_json,width,page_height,theme,photo_fit,title_font,body_font,manual_plan=''):
        plan=parse_plan(manual_plan.strip() or plan_json,photos['photos'])
        pages,long,report=render(photos['photos'],plan,photos['hotel_name'],width,page_height,
                                 theme,photo_fit,title_font,body_font)
        report['input_warnings']=photos['warnings']
        out=Path(folder_paths.get_output_directory())/'hotelshow_reports'
        out.mkdir(parents=True,exist_ok=True)
        name='hotelshow_'+uuid.uuid4().hex[:12]
        plan_text=json.dumps(plan,ensure_ascii=False,indent=2)
        (out/(name+'_plan.json')).write_text(plan_text,encoding='utf-8')
        report['plan_file']='hotelshow_reports/'+name+'_plan.json'
        report_text=json.dumps(report,ensure_ascii=False,indent=2)
        (out/(name+'_report.json')).write_text(report_text,encoding='utf-8')
        return {'ui':{'text':[report_text]},'result':(
            torch.cat([tensor_image(p) for p in pages]),tensor_image(long),report_text,plan_text)}
